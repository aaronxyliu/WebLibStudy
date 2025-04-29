# Crawl vulnerabilities from Synk database
# Use the following statement to analyze:
    # SELECT v.libname, l.star, l.`group`, l.`category`, l.`# hits`
    # FROM vulnerabilities AS v 
    # INNER JOIN libs_cdnjs_all_4_20u AS l ON v.libname=l.libname
    # GROUP BY v.libname, l.star, l.`group`, l.`category`, l.`# hits`;

    # SELECT l.category, COUNT(DISTINCT v.libname) 
    # FROM vulnerabilities AS v 
    # INNER JOIN libs_cdnjs_all_4_20u AS l ON v.libname=l.libname
    # GROUP BY l.category;

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

libraries = ["react", "angular", "vue"]  # your libraries

LIB_TABLE = 'libs_cdnjs_all_4_20u'
VUL_TABLE = 'vulnerabilities'
START_RANK = 2823
END_RANK = 1000000
CRAWL_INTERVAL = 0.5

def crawlFromSynk(libname):
    url = f"https://snyk.io/vuln/npm:{libname}"
    vul_num = 0

    # Fetch the page content
    response = requests.get(url)
    # response.raise_for_status()  # Raise an error if the request fails
    if response.status_code != 200:
        logger.warning(f"Could not fetch page: {url}")
        return 0

    # Parse the HTML content
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the target table
    target_table = soup.find('table', {
        'class': 'table',
        'data-snyk-test': 'PackageVulnerabilitiesTable: table'
    })

    if target_table:
        # Find the tbody with class "table__tbody" that is a direct child of the table
        tbody = target_table.find('tbody', class_='table__tbody', recursive=False)
        
        if tbody:
            # Find all direct child tr elements with class "table__row" of the tbody
            table_rows = tbody.find_all('tr', class_='table__row', recursive=False)
            
            # Process the rows
            for row in table_rows:
                # Find the anchor element with specified class and attributes
                anchor = row.find('a', {
                    'data-snyk-test': 'vuln table title'
                })
                
                if anchor:
                    # Extract href (URL) and text content
                    href = anchor.get('href', '').strip()
                    vulnerability_type = anchor.get_text(strip=True)

                    versions = [None] * 6
                    spans = row.find_all('span', class_='chip__value')
                    for i, version_span in enumerate(spans[:6]): 
                        # Only enumerate the first three version spans
                        versions[i] = version_span.get('title', '').strip()
                    
                    severity = None
                    abbr = row.find('abbr', class_='severity__text')
                    if abbr:
                        severity = abbr.get('title', '').strip()

                    db.upsert(table_name=VUL_TABLE, 
                              data={'libname': libname,
                                    'vulnerability': vulnerability_type,
                                    'severity': severity,
                                    'synk': href,
                                    'version1': versions[0],
                                    'version2': versions[1],
                                    'version3': versions[2],
                                    'version4': versions[3],
                                    'version5': versions[4],
                                    'version6': versions[5]},
                              condition_fields='synk')
                    vul_num += 1

                else:
                    logger.warning("Target anchor not found in the tbody.")
        else:
            logger.warning("Target tbody not found in the table.")
    else:
        logger.warning("Target table not found on the page.")

    return vul_num

def crawlAll():

    db.create_if_not_exists(VUL_TABLE, '''
        `libname` varchar(100) DEFAULT NULL,
        `vulnerability` varchar(200) DEFAULT NULL,
        `severity` varchar(100) DEFAULT NULL,
        `synk` varchar(500) DEFAULT NULL,
        `version1` varchar(500) DEFAULT NULL,
        `version2` varchar(500) DEFAULT NULL,
        `version3` varchar(500) DEFAULT NULL,
        `version4` varchar(500) DEFAULT NULL,
        `version5` varchar(500) DEFAULT NULL,
        `version6` varchar(500) DEFAULT NULL
    ''')

    # res = db.fetchall('SELECT libname FROM `vulnerabilities_backup` GROUP BY libname;')
    res = db.select_all(LIB_TABLE, ['cdnjs rank', 'libname'], return_as='tuple', order_by='cdnjs rank')
    
    for entry in res:
        rank, libname = entry[0], entry[1]
        if rank < START_RANK:
            continue
        if rank > END_RANK:
            break
        
        logger.info(f'Start crawling {rank}: {libname}')
        vul_num = crawlFromSynk(libname)
        logger.info(f'    {vul_num} vulnerabilities are founded.')
        time.sleep(CRAWL_INTERVAL)


if __name__ == '__main__':
    crawlAll()