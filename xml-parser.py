import xml.etree.ElementTree as ET
from xml.dom import minidom
import requests
import time
import os

def parse_xml(xml_content):
    root = ET.fromstring(xml_content)
    team_stats = {}
    
    # Extract team names from the venue element
    venue = root.find('.//venue')
    team_names = {
        'V': venue.get('visname'),
        'H': venue.get('homename')
    }
    
    for team in root.findall('.//team'):
        vh = team.get('vh')
        totals = team.find('totals')
        
        if totals is not None:
            rush = totals.find('rush')
            passing = totals.find('pass')
            firstdowns = totals.find('firstdowns')
            penalties = totals.find('penalties')
            misc = totals.find('misc')
            
            team_stats[team_names[vh]] = {
                'rush_yards': int(rush.get('yds', 0)) if rush is not None else 0,
                'pass_yards': int(passing.get('yds', 0)) if passing is not None else 0,
                'total_yards': int(totals.get('totoff_yards', 0)),
                'time_of_possession': misc.get('top', '00:00') if misc is not None else '00:00',
                'penalties': int(penalties.get('no', 0)) if penalties is not None else 0,
                'first_downs': int(firstdowns.get('no', 0)) if firstdowns is not None else 0
            }
    
    return team_stats

def fetch_and_parse(url):
    response = requests.get(url)
    if response.status_code == 200:
        return parse_xml(response.content)
    else:
        print(f"Failed to fetch XML. Status code: {response.status_code}")
        return None

def save_stats_xml(stats, filename):
    root = ET.Element("team_stats")
    
    for team_name, team_stats in stats.items():
        team_elem = ET.SubElement(root, "team")
        team_elem.set("name", team_name)
        
        for stat, value in team_stats.items():
            stat_elem = ET.SubElement(team_elem, stat.replace(" ", "_"))
            stat_elem.text = str(value)
    
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    with open(filename, 'w') as f:
        f.write(xml_str)

def main(url, interval=10, output_file="team_stats.xml"):
    while True:
        stats = fetch_and_parse(url)
        if stats:
            save_stats_xml(stats, output_file)
            print(f"Stats saved to {output_file}")
        time.sleep(interval)

if __name__ == "__main__":
    xml_url = "https://prestosports.com/action/stats/downloadXML.jsp?event_id=lpha0epkiq9wfvsp"  # Replace with your actual URL
    main(xml_url)