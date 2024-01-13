import requests
from bs4 import BeautifulSoup, Tag
from typing import List, Union, Tuple
import re
import sys
from tqdm import tqdm
import time




def get_book_name(soup: BeautifulSoup) -> str:
    title_element: Union[Tag, None] = soup.find('h1', class_='title')
    if title_element:
        return title_element.text.strip()
    else:
        return "unk"

def create_fb2_header(title: str) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<FictionBook xmlns="http://www.gribuser.ru/xml/fictionbook/2.0" xmlns:l="http://www.w3.org/1999/xlink">
  <description>
    <title-info>
      <genre>fiction</genre>
      <author><first-name>Unknown</first-name><last-name>Author</last-name></author>
      <book-title>{title}</book-title>
      <lang>ru</lang>
    </title-info>
  </description>
<body>
'''
def create_fb2_footer() -> str:
    return '''
</body>
</FictionBook>
'''

def save_paragraphs_as_FB2(book_name: str, paragraphs: List[Tag]) -> None:
    fb2_content: str = create_fb2_header(book_name)
    fb2_content += ''.join(f'<p>{paragraph.text.strip()}</p>\n' for paragraph in paragraphs)
    fb2_content += create_fb2_footer()
    with open(f'{book_name}.fb2', 'w', encoding='utf-8') as file:
        file.write(fb2_content)

def save_fb2_content(book_name: str, toc: List[str], content: List[str]) -> None:
    file_name = f'{book_name}.fb2'
    
    with open(file_name, 'w', encoding='utf-8') as file:
        file.write(create_fb2_header(book_name))
        file.writelines(content)
        if toc:  # Перевірка, чи зміст не порожній
            file.write('<body>\n<title>Зміст</title>\n')
            file.writelines(toc)
            file.write('</body>\n')
        file.write(create_fb2_footer())
        print(f"saved as '{file_name}'")

def count_xml_special_characters(paragraphs: List[Tag]) -> int:
    special_chars: List[str] = ['&', '<', '>']
    count: int = 0
    for paragraph in paragraphs:
        text: str = paragraph.text
        for char in special_chars:
            count += text.count(char)
    return count

def escape_xml_characters(paragraphs: List[Tag]) -> List[str]:
    escaped_paragraphs: List[str] = []
    for paragraph in paragraphs:
        escaped_text: str = paragraph.text.replace("&", "&amp;") \
                                          .replace("<", "&lt;") \
                                          .replace(">", "&gt;")
        escaped_paragraphs.append(escaped_text)
    return escaped_paragraphs

def get_soup(url):
    response = requests.get(url)
    html_content = response.content
    return BeautifulSoup(html_content, 'html.parser')

def extract_paragraphs_only(soup: BeautifulSoup) -> List[str]:
    paragraphs = soup.find_all('p', class_='book')

    special_chars_count = count_xml_special_characters(paragraphs)
    print(f"Special symbols count: {special_chars_count}")

    if special_chars_count > 0:
        mod_paragraphs = escape_xml_characters(paragraphs)
    else:
        mod_paragraphs = [paragraph.text.strip() for paragraph in paragraphs]
        
    return mod_paragraphs

# fb2_body.append(f'<p></p>\n')
# fb2_body.append(f'<p></p>\n')
# fb2_body.append(f'<p></p>\n')

            
def extract_book(soup: BeautifulSoup) -> Tuple[List[str], List[str]]:
    elements = soup.find_all(re.compile('^(h[1-6]|p)$'), class_='book')
    fb2_body: List[str] = []
    toc: List[str] = []
    chapter_counter: int = 1
    chapter_open = False

    for element in elements:
        if element.name.startswith('h'):
            if chapter_open:
                fb2_body.append('</section>\n')  # Закриття попередньої глави, якщо вона була відкрита
            chapter_title = element.text.strip()
            chapter_id = f'chapter{chapter_counter}'
            toc.append(f'<p><a l:href="#{chapter_id}">{chapter_title}</a></p>\n')
            fb2_body.append(f'<section id="{chapter_id}">\n')
            fb2_body.append(f'<title>{chapter_title}</title>\n')  # Додавання заголовка глави
            fb2_body.append(f'<p><strong>{chapter_title}</strong></p>\n')  # Додавання заголовка в текст книги
            chapter_counter += 1
            chapter_open = True
        else:
            text = element.text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            fb2_body.append(f'<p>{text}</p>\n')

    if chapter_open:
        fb2_body.append('</section>\n')  # Закриття останньої глави

    return toc, fb2_body


def get_book_from_flibusta(url):
    with tqdm(total=1, desc="   waiting") as progress_bar:
        start_time = time.time()
        soup = get_soup(url)  # Ваша функція для отримання soup з URL
        end_time = time.time()
        elapsed_time = end_time - start_time

        # Час очікування виводимо в секундах з двома знаками після коми
        progress_bar.set_postfix(Time=f"{elapsed_time:.2f}s")
        progress_bar.update(1)
        
    book_name = get_book_name(soup)
    print(f"   Book='{book_name}' - ", end=" ")

    toc, content = extract_book(soup)
    save_fb2_content(book_name, toc, content)


# get_book_from_flibusta("http://flibusta.site/b/759596/read")
# get_book_from_flibusta("http://flibusta.site/b/759597/read")
# get_book_from_flibusta("http://flibusta.site/b/759598/read")
# get_book_from_flibusta("http://flibusta.site/b/759369/read")

urls = [
    "http://flibusta.site/b/759596/read",
    "http://flibusta.site/b/759597/read",
    "http://flibusta.site/b/759598/read",
    "http://flibusta.site/b/759369/read"    
]

if __name__ == "__main__":
    if len(sys.argv) == 2:
        url = sys.argv[1]
        get_book_from_flibusta(url)
        print()
    else:
       for i, url in enumerate(urls):
           print(f"{i+1:2} Url={url}")
           get_book_from_flibusta(url)
           print()
           
