import argparse
import datetime as dt
import html
import os
import re
import unicodedata

from collections import namedtuple

import pandas as pd

SpeakerData = namedtuple('SpeakerData', 'id name link img talk description bio')

RE_SEARCH_BSKY = re.compile(r'@?([^\s]+\.bsky\.social)').search

CURSED_BR_PLACEHOLDER = '__RLC_PLACEHOLDER_BR__'

class Speakers:
    def __init__(self, fname):
        munged_html = ''
        with open(fname, 'r', encoding='utf-8') as f:
            file_data = f.read()
            munged_html = re.sub(r'<\s*br\s*/?\s*>', CURSED_BR_PLACEHOLDER, file_data)
        df = pd.read_html(munged_html, skiprows=1)[0]
        self.data = df[df['id'].notna()]
        assert self.data['id'].nunique() == self.data.shape[0], 'if this assertion fails, make sure the ids are unique before running this script'
        # print(self.data)

    def write_html_lines(self):
        out_lines = []
        get_value = lambda x: row[x] if isinstance(row[x], str) else '__RLC_PLACEHOLDER_BAD_SOURCE_DATA__'
        self.data.sort_values('name', key=lambda x: x.str.casefold(), inplace=True)
        for i, row in self.data.iterrows():
            talk_id = get_value('id')
            talk_title = get_value('talk_title')
            speaker_name = get_value('name')
            speaker_bio = get_value('biography').replace(CURSED_BR_PLACEHOLDER, '\n')
            speaker_img = row['headshot'] if isinstance(row['headshot'], str) else './photos/2025/placeholder.png'
            link = self._attempt_to_fix_links(row['social_media_link']) if isinstance(row['social_media_link'], str) else None
            out_lines.extend(get_speaker(talk_id, talk_title, speaker_name, speaker_bio, speaker_img, link).splitlines())
        return out_lines

    def _get_talk_id(self, talk_title, speaker_name):
        # yeah this is kinda horrible and I think if I were rewriting it I'd do it differently, but...
        names = [y for x in re.split(r'\b(?:,|and|&)\b', speaker_name) if (y := x.strip())]
        pattern = '|'.join(rf'\b{n}\b' for n in names)
        # print(f'{speaker_name} -> {names}')
        name_result = self.data.loc[self.data['name'].str.contains(pattern, flags=re.IGNORECASE, regex=True)]
        talk_title_result = self.data.loc[self.data['talk_title'].str.contains(talk_title, case=False, regex=False, na=False)]

        if name_result.shape[0] == 1 and talk_title_result.shape[0] == 1:
            name_result_talk_id = name_result.iloc[0]['id']
            talk_title_result_talk_id = name_result.iloc[0]['id']
            if name_result_talk_id == talk_title_result_talk_id:
                return name_result_talk_id
            else:
                raise RuntimeError('please check this manually?')

        if name_result.shape[0] == 0:
            names = [n.split() for n in names]
            flattened_names = [n for i in names for n in i]
            # print(f'no name match for "{speaker_name}"; trying {flattened_names}')
            pattern = '|'.join(rf'\b{n}\b' for n in flattened_names)
            name_result = self.data.loc[self.data['name'].str.contains(pattern, flags=re.IGNORECASE, regex=True)]
            if name_result.shape[0] == 0:
                raise RuntimeError(f'no name match for "{speaker_name}"')

        if name_result.shape[0] > 1:
            if talk_title_result.shape[0] == 1:
                return talk_title_result.iloc[0]['id']
            if talk_title_result.shape[0] == 0:
                raise RuntimeError('multiple name matches, but no exact match (no exact title match either)')
            raise RuntimeError('???')

        # print(f'check next entry ("{speaker_name}") manually!')
        return name_result.iloc[0]['id']

    def _compare(self, a, b):
        norm = lambda x: unicodedata.normalize('NFKC', x.strip()).casefold()
        return norm(a) == norm(b)

    def _print_on_mismatch(self, a, b):
        try:
            if not self._compare(a, b):
                print(f'{a} -> {b}')
        except AttributeError as e:
            print(f'unable to compare "{a}" to "{b}": {e}')

    def _get_row(self, talk_title, speaker_name):
        talk_id = self._get_talk_id(talk_title, speaker_name)
        result = self.data.loc[self.data['id'] == talk_id]
        assert result.shape[0] == 1
        out = result.iloc[0]
        self._print_on_mismatch(speaker_name, out['name'])
        self._print_on_mismatch(talk_title, out['talk_title'])
        return out

    def _attempt_to_fix_links(self, data):
        if data.strip().casefold().startswith('http'):
            return data.strip()
        match = RE_SEARCH_BSKY(data)
        if match:
            return f'https://bsky.app/profile/{match.group(1)}'
        return f'__RLC_PLACEHOLDER_BAD_SOURCE_DATA_\'({data})\'__'

    def get_canonical_talk_data(self, talk_title, speaker_name):
        data = self._get_row(talk_title, speaker_name)
        talk_id = data['id']
        canonical_talk_title = data['talk_title']
        if not isinstance(canonical_talk_title, str):
            canonical_talk_title = talk_title
            print(f'verify manually: talk title "{canonical_talk_title}" is from internal scheduling spreadsheet; not found in speaker data')
        talk_description = data['talk_description'].replace(CURSED_BR_PLACEHOLDER, '\n')
        name = data['name']
        return talk_id, canonical_talk_title, talk_description, name

ScheduleItem = namedtuple('ScheduleItem', 'time activity talk speaker')

def get_speaker(talk_id, talk_title, speaker_name, speaker_bio, speaker_img, link):
    link_href = f' href="{link}"' if link else ''
    speaker_bio_html = '\n'.join(f'<p>{html.escape(y)}</p>' for x in speaker_bio.splitlines() if (y := x.strip()))
    return f'''
<div class="speaker" id="{talk_id}">
    <div class="link">
        <a target="_blank" class="social_media_link"{link_href}>
            <img class="headshot" src="./photos/2026/{speaker_img}">
        </a>
    </div>
    <div class="talk">
        <a target="_blank" class="social_media_link"{link_href}>
            <div class="speaker-name">{html.escape(speaker_name)}</div>
        </a>
        <div><a class="talk_link" href="event2026.html#{talk_id}">{html.escape(talk_title)}</a></div>
        <div class="bio">{speaker_bio_html}</div>
    </div>
</div>
<hr>'''.strip()

def get_talk_block(activity, timedate_pdt, talk_id, title, description, speaker):
    block_class = f' {activity}' if activity else ''
    when_pdt = timedate_pdt.strftime('%H:%M')
    when_pdt = when_pdt[1:] if (timedate_pdt.hour > 0 and timedate_pdt.hour < 10) else when_pdt
    timedate_utc = timedate_pdt.astimezone(dt.timezone.utc)
    when_utc = timedate_utc.strftime('%H:%M')
    description_html = '\n'.join(f'<p>{html.escape(y)}</p>' for x in description.splitlines() if (y := x.strip()))
    return f'''
<div class="block{block_class}">
  <div class="when">{when_pdt}</div>
  <div class="when"><time datetime="{timedate_utc.isoformat().replace('+00:00', 'Z')}">{when_utc}</time></div>
  <div class="what">
    <div class="talk-title">
      <span class="anchor" id="{talk_id}"></span>
      <details name="talks">
        <summary>{html.escape(title)}</summary>
        <div class="bio">
          {description_html}
        </div>
      </details>
    </div>
    <div class="speakers"><a href="speakers2026.html#{talk_id}">{html.escape(speaker)}</a></div>
  </div>
</div>'''.strip()


def get_nontalk_block(activity, timedate_pdt, title):
    block_class = f' {activity}' if activity else ''
    when_pdt = timedate_pdt.strftime('%H:%M')
    when_pdt = when_pdt[1:] if (timedate_pdt.hour > 0 and timedate_pdt.hour < 10) else when_pdt
    timedate_utc = timedate_pdt.astimezone(dt.timezone.utc)
    when_utc = timedate_utc.strftime('%H:%M')
    return f'''
<div class="block{block_class}">
  <div class="when">{when_pdt}</div>
  <div class="when"><time datetime="{timedate_utc.isoformat().replace('+00:00', 'Z')}">{when_utc}</time></div>
  <div class="what">
    <div class="talk-title">{title}</div>
  </div>
</div>'''.strip()

class DaySchedule:
    def __init__(self, speakers, date_pdt, df):
        self.speakers = speakers
        self.date_pdt = dt.date.fromisoformat(date_pdt)
        self.df = df
        self.data = []
        self.build_schedule()
        # self.activity_types = set(x.activity for x in self.data)
        # print(self.activity_types)

    def build_schedule(self):
        last_activity = None
        last_talk = None
        last_speaker = None
        for i, row in self.df.iterrows():
            current_time = row['Time (PDT)'].strip() if pd.notna(row['Time (PDT)']) else None
            current_activity = row['Activity'].strip() if pd.notna(row['Activity']) else None
            current_talk = row['Talk Name'].strip() if pd.notna(row['Talk Name']) else None
            current_speaker = row['Speaker'].strip() if pd.notna(row['Speaker']) else None
            activity_changed = current_activity and (current_activity != last_activity)
            talk_changed = current_talk and (current_talk != last_talk)
            speaker_changed = current_speaker and (current_speaker != last_speaker)
            if activity_changed or talk_changed or speaker_changed:
                hh_time = current_time if int(current_time.split(':')[0]) > 9 else f'0{current_time}' # sorry this is so ugly
                time = dt.time.fromisoformat(f'{hh_time}:00-07:00') # expects PDT
                self.data.append(ScheduleItem(dt.datetime.combine(self.date_pdt, time, time.tzinfo), current_activity, current_talk, current_speaker))
            last_activity = current_activity
            last_talk = current_talk
            last_speaker = current_speaker

    @staticmethod
    def get_activity_title_from_activity(activity):
        match activity:
            case 'Social':
                return 'social time'
            case 'Announcements':
                return 'kickoff'
            case 'Unconferencing':
                return 'unconferencing'
            case 'Space Closes':
                return 'social space closes'
            case _:
                print(f'unhandled activity title: {activity}')
                return activity


    @staticmethod
    def get_class_from_activity(activity):
        match activity:
            case 'Social':
                return 'social'
            case 'Full Talk':
                return 'full'
            case 'Lightning':
                return 'lightning'
            case 'Announcements':
                return 'kickoff'
            case 'Unconferencing':
                return 'unconferencing'
            case 'Space Closes':
                return 'social'
            case _:
                print(f'unhandled activity badge (treated as full talk): {activity}')
                return 'full'

    def write_html_lines(self, article_id):
        # sorry this feels kinda icky writing html with strings
        # (also just, like, indent the result in an IDE after getting the output from here, I guess)
        out_lines = []
        out_lines.append(f'<article class="schedule" id="{article_id}">')
        out_lines.append(f'<h2>{self.date_pdt:%A, %B %d, %Y}</h2>') # you may need to remove leading zeros from the 0 padded dates? *shrug*
        out_lines.extend('''
<div class="block header">
  <div class="when">PDT</div>
  <div class="when">UTC</div>
  <div class="what"><span style="color:cyan">S</span>: social time; <span style="color:orange">F</span>: full talk; <span style="color:yellow">L</span>: lightning talk; U: unconferencing</div>
</div>
'''.strip().splitlines())
        for item in self.data:
            if item.speaker:
                talk_id, canonical_talk_title, talk_description, name = self.speakers.get_canonical_talk_data(item.talk, item.speaker)
                out_lines.extend(get_talk_block(DaySchedule.get_class_from_activity(item.activity), item.time, talk_id, canonical_talk_title, talk_description, name).splitlines())
            else:
                out_lines.extend(get_nontalk_block(DaySchedule.get_class_from_activity(item.activity), item.time, DaySchedule.get_activity_title_from_activity(item.activity)).splitlines())
        out_lines.append(f'</article>')
        return out_lines

class EventSchedule:
    COLS_PER_DAY = 5

    def __init__(self, speakers, fname):
        self.speakers = speakers
        # sorry, just edit these hardcoded things
        self.days = [
            DaySchedule(self.speakers, '2026-10-17', self._parse(fname, EventSchedule._get_cols_for_day('A'))),
            DaySchedule(self.speakers, '2026-10-18', self._parse(fname, EventSchedule._get_cols_for_day('H')))
        ]

    @staticmethod
    def _get_cols_for_day(start_col_name):
        start_col_idx = ord(start_col_name.strip().upper()) - ord('A')
        return list(range(start_col_idx, start_col_idx + EventSchedule.COLS_PER_DAY))

    def _parse(self, fname, cols):
        out = pd.read_csv(fname, delimiter='\t', header=1, usecols=cols)
        if 'Time (PDT)' not in out.columns:
            out.rename(columns={x: re.sub(r'\.\d+$', '', x) for x in out.columns}, inplace=True)
        return out

    def count_talks(self):
        # non_talks = ['Social', 'Unconferencing', 'Space Closes', 'Announcements']
        # is_talk = lambda x: (x is None) or (not any(x.casefold() in y.casefold() for y in non_talks))
        count = 0
        for day in self.days:
            # talks = [x for x in day.data if is_talk(x.activity)]
            talks = [x for x in day.data if x.speaker]
            count += len(talks)
        return count

def main():
    parser = argparse.ArgumentParser(description='Creates HTML fragments for schedule and speaker bio from spreadsheet data')
    parser.add_argument('-r', '--responses', required=True, help='Path to collated speaker responses html (as downloaded from Google Sheets)')
    parser.add_argument('-s', '--schedule', required=True, help='Path to schedule tsv')
    parser.add_argument('-o', '--output', required=False, help='Path to destination directory (optional, defaults to working directory if unspecified)')
    args = parser.parse_args()

    speakers = Speakers(args.responses)
    event_schedule = EventSchedule(speakers, args.schedule)

    destination_directory = args.output if args.output else ''

    day_ids = ['saturday', 'sunday']
    for i, day in enumerate(day_ids):
        destination_path = os.path.join(destination_directory, f"{day}.html")
        out_lines = event_schedule.days[i].write_html_lines(day)
        with open(destination_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out_lines))

    out_lines = speakers.write_html_lines()
    destination_path = os.path.join(destination_directory, f"speakers.html")
    with open(destination_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))

if __name__ == '__main__':
    main()