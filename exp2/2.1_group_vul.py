# Standardize the vulnerability names crawled from Synk database

import requests
import time
from bs4 import BeautifulSoup
import sys
from pathlib import Path
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))
from utils.sqlHelper import ConnDatabase
from utils.logger import getLogger
logger = getLogger()
db = ConnDatabase('Libraries')

VUL_TABLE = 'vulnerabilities'

VULNERABILITY_GROUPS = [
    {
        "primary": "Injection",
        "keywords": ["injection", "inject"],
        "variants": [
            "SQL Injection",
            "Code Injection",
            "Command Injection",
            "HTML Injection",
            "CSS Injection",
            "Template Injection",
            "Content Injection",
            "VBScript Content Injection",
            "Arbitrary Script Injection",
            "Arbitrary Code Injection",
            "Multiple Content Injection Vulnerabilities",
            "Content Injection via TileJSON attribute",
            "Content Injection via TileJSON Name",
            "JSONP Callback Attack",
            "Relative Path Overwrite (RPO)"
        ]
    },
    {
        "primary": "Cross-site Scripting (XSS)",
        "keywords": ["xss", "cross-site scripting"],
        "variants": [
            "Cross-site Scripting",
            "Reverse Tabnabbing",
            "Content Security Policy (CSP) Bypass"
        ]
    },
    {
        "primary": "Cross-site Request Forgery (CSRF)",
        "keywords": ["csrf", "cross-site request forgery"],
        "variants": []
    },
    {
        "primary": "Authentication Bypass",
        "keywords": ["authentication bypass", "improper authentication"],
        "variants": [
            "Improper Authentication",
            "Access Restriction Bypass",
            "Authentication Bypass by Spoofing",
            "Protection Bypass",
            "Signature Bypass",
            "Validation Bypass",
            "Improper Restriction of Security Token Assignment"
        ]
    },
    {
        "primary": "Remote Code Execution (RCE)",
        "keywords": ["remote code execution", "rce", "arbitrary code execution"],
        "variants": [
            "Remote Code Execution",
            "Arbitrary Command Execution",
            "Arbitrary Code Execution",
            "Code Execution due to Deserialization",
            "Arbitrary File Upload"
        ]
    },
    {
        "primary": "Server-side Request Forgery (SSRF)",
        "keywords": ["ssrf", "server-side request forgery"],
        "variants": []
    },
    {
        "primary": "Denial of Service (DoS)",
        "keywords": ["denial of service", "dos"],
        "variants": [
            "Regular Expression Denial of Service (ReDoS)",
            "Infinite loop",
            "Out of Memory Crash",
            "Buffer Overflow",
            "Memory Corruption",
            "Remote Memory Exposure"
        ]
    },
    {
        "primary": "Information Exposure",
        "keywords": ["information exposure", "data exposure"],
        "variants": [
            "Insufficiently Protected Credentials",
            "Insecure Credential Storage",
            "Observable Discrepancy"
        ]
    },
    {
        "primary": "Unsafe Deserialization",
        "keywords": ["deserialization"],
        "variants": [
            "Deserialization of Untrusted Data",
            "Unsafe Object Deserialization",
            "Code Execution due to Deserialization"
        ]
    },
    {
        "primary": "Cryptographic Issues",
        "keywords": ["cryptographic", "crypto"],
        "variants": [
            "Cryptographic Weakness",
            "Use of a Broken or Risky Cryptographic Algorithm",
            "Insecure Randomness",
            "Improper Verification of Cryptographic Signature",
            "Timing Attack"
        ]
    },
    {
        "primary": "Validation Issues",
        "keywords": ["input validation", "improper validation"],
        "variants": [
            "Improper Input Validation",
            "Insufficient Validation",
            "Improper Validation of Specified Type of Input",
            "Improper Validation of Unsafe Equivalence in Input",
            "Incomplete Filtering of Special Elements",
            "Improper Handling of Exceptional Conditions",
            "Insufficient Verification of Data Authenticity",
            "Uncaught Exception",
            "Undesired Behavior"
        ]
    },
    {
        "primary": "Privilege Escalation",
        "keywords": ["privilege escalation"],
        "variants": ["Directory Traversal"]
    },
    {
        "primary": "Clickjacking",
        "keywords": ["clickjacking"],
        "variants": []
    },
    {
        "primary": "DNS Rebinding",
        "keywords": ["dns rebinding"],
        "variants": []
    },
    {
        "primary": "Prototype Pollution",
        "keywords": ["prototype pollution"],
        "variants": [
            "Internal Property Tampering"
        ]
    },
    {
        "primary": "Insecure Configuration",
        "keywords": ["insecure config", "insecure default"],
        "variants": [
            "Insecure Default Configuration",
            "Insecure Defaults",
            "Outdated Static Dependency"
        ]
    },
    {
        "primary": "Malicious Code",
        "keywords": ["supply chain", "malicious package"],
        "variants": [
            "Malicious Package",
            "Embedded Malicious Code"
        ]
    }
]

GROUP_MAPPING = {}

for entry in VULNERABILITY_GROUPS:
    for var in entry['variants']:
        GROUP_MAPPING[var] = entry['primary']


if __name__ == '__main__':
    db.add_column(VUL_TABLE, 'vgroup', 'varchar(100) DEFAULT NULL', after_column='vulnerability')   # vulnerability group

    res = db.select_all(VUL_TABLE, ['vulnerability', 'synk'])
    for entry in res:
        vul, synk = entry['vulnerability'], entry['synk']
        
        group = vul
        if vul in GROUP_MAPPING:
            group = GROUP_MAPPING[vul]
            
        db.update(VUL_TABLE, {'vgroup': group}, "`synk`=%s", (synk,))
    db.close()