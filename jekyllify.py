import os
from lxml import html
from pprint import pprint
from jinja2 import Template, Markup

SEGMENT = """---
layout: default
title: {{title.replace(':', '&59;')}}
short_title: {{short_title.replace(':', ' -')}}
---

<div class="btn-group book-nav-top">
    <a class='btn' href="index.html">Home</a>
    {% if parent_name %}
        <a href="{{parent_name}}.html" class="btn">Chapter: {{parent_title}}</a>
    {% endif %}
    {% if next_name %}
        <a href="{{next_name}}.html" class="btn">Next: {{next_title.rsplit('(',1)[0]}}</a>
    {% endif %}
</div>

<div id='content'>
    {{body}}
</div>

{% if children %}
    <h3>What's in this chapter?</h3>
    <ul class='toc'>
        {% for c in children %}
            <li><a href="{{c.name}}.html">{{c.short_title}}</a></li>
        {% endfor %}
    </ul>
{% endif %}

<div class="btn-group book-nav-bottom">
    <a class='btn' href="index.html">Home</a>
    {% if parent_name %}
        <a href="{{parent_name}}.html" class="btn">Chapter: {{parent_title}}</a>
    {% endif %}
    {% if next_name %}
        <a href="{{next_name}}.html" class="btn">Next: {{next_title.rsplit('(',1)[0]}}</a>
    {% endif %}
</div>
"""

INDEX = """---
layout: default
title: Index
---

<div class="row">
    <div class='span6'>
        {% for chapter in segments %}
        {% if not chapter.parent_name and chapter.name != 'preface' %}
            <h2><a href='{{chapter.name}}.html'>{{chapter.title}}</a></h2>
            <ul class='toc'>
                {% for segment in chapter.children %}
                    <li><a href="{{segment.name}}.html">{{segment.short_title}}</a></li>
                {% endfor %}
            </ul>
        {% endif %}
        {% endfor %}
    </div>
    <div class='span6'>
        <div class='well'>
            <img src='img/cover_print.png' align='center'>
        </div>
    </div>
</div>

"""


def write_segment(data, out_dir):
    content = Template(SEGMENT).render(data)
    write_file(content, out_dir, data.get('name'))


def write_index(segments, out_dir):
    content = Template(INDEX).render(segments=segments)
    write_file(content, out_dir, 'index')


def write_file(content, out_dir, name):
    file_name = os.path.join(out_dir, name + '.html')
    fh = file(file_name, 'wb')
    fh.write(content.encode('utf-8'))
    fh.close()


def split_up(in_file, out_dir):
    segments = []
    doc = html.parse(in_file)
    for sect1 in doc.findall('//div[@class="sect1"]'):
        sect1_title = sect1.find('h2')
        name = sect1_title.get('id').strip('_')
        sect1_title_text = sect1_title.text
        for i, sect2 in enumerate(sect1.findall('.//div[@class="sect2"]')):
        #    #print dir(sect2)
            sect2_title = sect2.find('h3')
            segments.append({
                'name': name + '_' + str(i),
                'title': sect2_title.text,
                'body': html.tostring(sect2),
                'el': sect2,
                'parent_name': name,
                'parent_title': sect1_title_text
                })
            sect2.getparent().remove(sect2)
        segments.append({
            'name': name,
            'title': sect1_title_text,
            'body': html.tostring(sect1),
            'el': sect1,
            'parent_name': None,
            'parent_title': None
            })

    for segment in segments:
        segment['short_title'] = segment['title'].rsplit('(')[0]
        segment['children'] = filter(lambda s: s['parent_name'] == segment['name'], segments)

    sorted_segments = []
    for segment in segments:
        if segment['parent_name']:
            continue
        sorted_segments.append(segment)
        for s in segment.get('children', []):
            s['parent'] = segment
            sorted_segments.append(s)

    for i, segment in enumerate(sorted_segments):
        if i < len(sorted_segments) - 1:
            if len(segment['children']):
                for s in sorted_segments[i + 1:]:
                    if len(s['children']):
                        segment['next_title'] = s['title']
                        segment['next_name'] = s['name']
                        break
            else:
                segment['next_title'] = sorted_segments[i+1]['title']
                segment['next_name'] = sorted_segments[i+1]['name']
        #pprint(segment)
        write_segment(segment, out_dir)
    write_index(sorted_segments, out_dir)

if __name__ == '__main__':
    split_up('book.html', 'web')
