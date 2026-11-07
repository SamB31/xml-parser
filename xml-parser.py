#!/usr/bin/env python3
"""
xml_stats_collector.py

Fetches game stats XML from a PrestoSports URL using Cloudflare bypass (cloudscraper),
parses out team statistics, and writes them to a local XML file on a recurring interval.

Requirements:
    pip install cloudscraper
"""

import sys
import time
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import cloudscraper


def fetch_xml(url: str, timeout: int = 30) -> str:
    """
    Uses cloudscraper to handle Cloudflare JS challenges and fetch raw XML as text.
    """
    scraper = cloudscraper.create_scraper(
        browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
    )
    resp = scraper.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def parse_xml(xml_content: str):
    root = ET.fromstring(xml_content)
    team_stats = {}
    venue = root.find('.//venue')
    team_names = {'V': venue.get('visname'), 'H': venue.get('homename')}

    for team in root.findall('.//team'):
        vh = team.get('vh')
        totals = team.find('totals')
        if totals is None:
            continue
        rush    = totals.find('rush')
        passing = totals.find('pass')
        firstds = totals.find('firstdowns')
        pens    = totals.find('penalties')
        misc    = totals.find('misc')

        stats = {
            'rush_yards':         int(rush.get('yds', 0))    if rush    is not None else 0,
            'pass_yards':         int(passing.get('yds', 0)) if passing is not None else 0,
            'total_yards':        int(totals.get('totoff_yards', 0)),
            'time_of_possession': misc.get('top', '00:00')    if misc    is not None else '00:00',
            'penalties':          int(pens.get('no', 0))      if pens    is not None else 0,
            'first_downs':        int(firstds.get('no', 0))   if firstds is not None else 0
        }
        team_stats[team_names[vh]] = stats

    return team_stats, team_names


def save_stats_xml(stats: dict, filename: str, team_names: dict, home_team: str, vis_team: str):
    root = ET.Element('team_stats')
    prefix_map = {team_names['H']: home_team, team_names['V']: vis_team}

    for team_name, data in stats.items():
        prefix = prefix_map.get(team_name, team_name.lower().replace(' ', '_'))
        for stat, val in data.items():
            tag = f"{prefix}_{stat.replace(' ', '_')}"
            elem = ET.SubElement(root, tag)
            elem.text = str(val)

    pretty = minidom.parseString(ET.tostring(root)).toprettyxml(indent='  ')
    script_dir = os.path.dirname(
        sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__)
    )
    path = os.path.join(script_dir, filename)
    with open(path, 'w') as f:
        f.write(pretty)


def main(interval: int = 10, output_file: str = 'team_stats.xml'):
    xml_url = input('Enter the XML URL: ').strip()
    home_tm = input('Enter the home team name (lowercase, no spaces): ').strip()
    away_tm = input('Enter the away team name (lowercase, no spaces): ').strip()

    try:
        while True:
            # fetch and parse
            try:
                xml_text = fetch_xml(xml_url)
            except Exception as e:
                print(f"Fetch error: {e}")
                time.sleep(interval)
                continue

            stats, team_names = parse_xml(xml_text)
            if stats:
                save_stats_xml(stats, output_file, team_names, home_tm, away_tm)
                print(f"[{time.strftime('%H:%M:%S')}] Stats saved to {output_file}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] No stats parsed.")

            time.sleep(interval)
    except KeyboardInterrupt:
        print('\nInterrupted by user, exiting.')

# https://prestosports.com/action/stats/downloadXML.jsp?event_id=lpha0epkiq9wfvsp
if __name__ == '__main__':
    main()
