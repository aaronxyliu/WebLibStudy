import json
from datetime import datetime
from urllib.request import Request, urlopen
import time
import os
import logging
from typing import Optional, Tuple, Dict, Any, List

default_logger = logging.getLogger(__name__)

class GitHubAPIReader:
    """
    A library for reading GitHub API content with multiple token support and rate limit handling.
    
    Features:
    - Multiple token rotation when rate limits are reached
    - Automatic rate limit detection and recovery
    - Token usage statistics tracking
    - Consecutive failure tracking
    """
    
    def __init__(self, tokens: Optional[List[str]] = None, logger: object = None, debug: bool = False):
        """
        Initialize the GitHub API reader with multiple tokens.
        
        Args:
            tokens: List of GitHub personal access tokens. If None, tries to get from GITHUB_TOKENS env var.
            logger: optional logger
        """
        self.consecutive_failures = 0
        self.tokens = tokens or os.getenv("GITHUB_TOKEN", "").split(",")
        
        if logger:
            self.logger = logger
        else:
            self.logger = default_logger

        if not self.tokens:
            self.self.logger.warning("No GitHub tokens provided. Unauthenticated requests have lower rate limits.")
        
        # Initialize token tracking
        self.token_status = {
            token: {
                'remaining': 5000,
                'reset_time': None,
                'last_used': None,
                'failures': 0
            } for token in self.tokens
        }
        self.debug = debug
        self.current_token_index = 0 if self.tokens else -1
    
    def _get_current_token(self) -> Optional[str]:
        """Get the currently active token."""
        if not self.tokens or self.current_token_index == -1:
            return None
        return self.tokens[self.current_token_index]
    
    def _rotate_token(self) -> None:
        """Rotate to the next available token and return it."""
        if not self.tokens:
            return None
            
        original_index = self.current_token_index
        rotated = False
        
        for _ in range(len(self.tokens)):
            self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
            current_token = self._get_current_token()
            status = self.token_status[current_token]
            
            # Skip tokens that are rate limited
            if status['remaining'] > 0 or (
                status['reset_time'] and status['reset_time'] <= datetime.now()
            ):
                if original_index != self.current_token_index:
                    if self.debug:
                        self.logger.info(f"Rotated to token ending with ...{current_token[-4:]}")
                    rotated = True
                return current_token
        
        # If all tokens are rate limited, return current one anyway
        if not rotated and original_index != self.current_token_index:
            current_token = self._get_current_token()
            if self.debug:
                self.logger.info(f"All tokens rate limited, using ...{current_token[-4:]}")
        return current_token
    
    def _get_best_token(self) -> Optional[str]:
        """Get the token with the most remaining requests."""
        if not self.tokens:
            return None
            
        # Filter tokens that aren't rate limited
        available_tokens = [
            (token, status['remaining'])
            for token, status in self.token_status.items()
            if status['remaining'] > 0 or 
               (status['reset_time'] and status['reset_time'] <= datetime.now())
        ]
        
        if not available_tokens:
            return None
            
        # Return token with highest remaining requests
        best_token = max(available_tokens, key=lambda x: x[1])[0]
        
        # Update current token index if we're switching to a better one
        if best_token != self._get_current_token():
            self.current_token_index = self.tokens.index(best_token)
            if self.debug:
                self.logger.info(f"Selected best available token ending with ...{best_token[-4:]}")
        
        return best_token
    
    def _wait_for_rate_limit_reset(self, token: str) -> None:
        """Wait until the rate limit resets for a specific token."""
        if not token:
            return
            
        status = self.token_status.get(token)
        if status and status['reset_time']:
            now = datetime.now()
            if status['remaining'] <= 0 and now < status['reset_time']:
                wait_seconds = (status['reset_time'] - now).total_seconds()
                self.logger.warning(f"Token ...{token[-4:]} rate limited. Waiting {wait_seconds:.1f} seconds...")
                time.sleep(wait_seconds + 1)  # Add 1 second buffer
    
    def _update_token_status(self, token: str, response) -> None:
        """Update the status of a token after a successful request."""
        if not token or token not in self.token_status:
            return
            
        self.token_status[token]['remaining'] = int(response.getheader('X-RateLimit-Remaining', 0))
        reset_timestamp = response.getheader('X-RateLimit-Reset')
        
        if reset_timestamp:
            self.token_status[token]['reset_time'] = datetime.fromtimestamp(int(reset_timestamp))
        
        self.token_status[token]['last_used'] = datetime.now()
        self.token_status[token]['failures'] = 0
    
    def _mark_token_failure(self, token: str) -> None:
        """Record a failure for a token."""
        if token and token in self.token_status:
            self.token_status[token]['failures'] += 1
    
    def read_url(self, url: str, max_retries: int = 3) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        Read content from a GitHub API URL with rate limit handling and token rotation.
        
        Args:
            url: The GitHub API URL to read
            max_retries: Maximum number of retries if rate limited
            
        Returns:
            Tuple of (response_data, should_stop)
            response_data: Parsed JSON response or None if failed
            should_stop: True if we should stop making requests (permanent failure)
        """
        stop_flag = False
        retry_count = 0

        
        
        while retry_count <= max_retries:
            # Select the best available token (this may rotate the token)
            current_token = self._get_best_token() if self.tokens else None
            
            if not current_token and self.tokens:
                # All tokens are rate limited - find the one that resets soonest
                soonest_reset = min(
                    (status['reset_time'] for status in self.token_status.values() 
                     if status['reset_time']),
                    default=None
                )
                
                if soonest_reset:
                    wait_time = (soonest_reset - datetime.now()).total_seconds()
                    self.logger.warning(f"All tokens rate limited. Waiting {wait_time:.1f} seconds...")
                    time.sleep(max(wait_time, 0) + 1)
                    continue
                else:
                    self.logger.error("All tokens exhausted with unknown reset times")
                    return None, True
            
            # Wait if current token is rate limited
            self._wait_for_rate_limit_reset(current_token)
            
            # Prepare the request with the current token
            req = Request(url)
            if current_token:
                req.add_header('Authorization', f'token {current_token}')
                if self.debug:
                    self.logger.debug(f"Using token ending with ...{current_token[-4:]}")
            
            try:
                # Make the request
                with urlopen(req) as response:
                    if current_token:
                        self._update_token_status(current_token, response)
                    
                    self.consecutive_failures = 0  # Reset on success
                    
                    # Parse and return the response
                    response_data = json.loads(response.read())
                    return response_data, False
                    
            except KeyboardInterrupt:
                self.logger.info("Request interrupted by user")
                return None, True
                
            except Exception as e:
                self.consecutive_failures += 1
                if current_token:
                    self._mark_token_failure(current_token)
                    # Rotate to next token for the next attempt
                    self._rotate_token()
                
                self.logger.warning(f"Request failed ({retry_count + 1}/{max_retries}): {str(e)}")
                
                if self.consecutive_failures >= 5:
                    self.logger.error("Too many consecutive failures, stopping")
                    return None, True
                
                # Exponential backoff for retries
                time.sleep(2 ** retry_count)
                retry_count += 1
        
        # If we exhausted retries
        self.logger.error(f"Failed after {max_retries} retries for URL: {url}")
        return None, False
    
    def get_usage_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get current usage statistics for all tokens."""
        return {
            f"...{token[-4:]}": {
                'remaining': status['remaining'],
                'reset_time': status['reset_time'].isoformat() if status['reset_time'] else None,
                'last_used': status['last_used'].isoformat() if status['last_used'] else None,
                'failures': status['failures']
            }
            for token, status in self.token_status.items()
        }
    

class commonReader:
    def __init__(self, logger: object = None, debug:bool = False):
        if logger:
            self.logger = logger
        else:
            self.logger = default_logger
        self.debug = debug

    def read_jsDelivr(self, libname:str, source:str, version_tag:str=None, period:str=None, stats:bool = True):
        """
        Read statistics content from jsDelivr API.
        API Reference: https://www.jsdelivr.com/docs/data.jsdelivr.com
        
        Args:
            libname: library name for npm. "owener/repo" for github
            source: "npm" or "gh"
            version_tag: [optional] the version name
            period: [optional] e.g. "day", "week", "year“
            stats: whether crawl the stats; otherwise crawl metainfo of the library
            
        Returns:
            response_data: Parsed JSON response or None if failed
        """
        if stats:
            base_url = f"https://data.jsdelivr.com/v1/stats/packages/{source}/{libname}"
        else:
            base_url = f"https://data.jsdelivr.com/v1/packages/{source}/{libname}"
        
        if version_tag:
            base_url += f"@{version_tag}"
        
        if period:
            base_url += f"?period={period}"

        if self.debug:
            self.logger.debug(f'Visit: {base_url}')
        req = Request(
            url=base_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        try:
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except KeyboardInterrupt:
            self.logger.info("Request interrupted by user")
            return None
        except Exception as e:
            self.logger.warning(f"Error processing {libname}: {e}")
        
        return None
    
    def read_npm(self, libname:str):
        base_url = f"https://registry.npmjs.org/{libname}"

        if self.debug:
            self.logger.debug(f'Visit: {base_url}')
        req = Request(
            url=base_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        try:
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data
        except KeyboardInterrupt:
            self.logger.info("Request interrupted by user")
            return None
        except Exception as e:
            self.logger.warning(f"Error processing {libname}: {e}")
        
        return None
