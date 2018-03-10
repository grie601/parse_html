import os
import re
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

BASE_dir = os.path.dirname(os.path.abspath(__file__))


class SetupHtml(object):
    @staticmethod
    def get_html(response):
        try:
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print("-get_html-" + str(e))
            return ''

    @staticmethod
    def get_response(url):
        try:
            response = requests.get(url)
        except Exception as e:
            print("-get_response-", e, url)
            return ''

        return response


class ParseHtml:
    def __init__(self, settings_html, site):
        self.settings_html = settings_html
        self.url = site
        self.content = self.get_content(self.url)

    @staticmethod
    def prepare_html(content):
        """
        подготавливаем страницу, каждый тэг начинаем с новой строки
        :param content:
        :return:
        """
        new_content = ''
        for line in str(content).split('>'):
            new_content += line + '>' + '\n'
        return new_content

    @staticmethod
    def get_body(content):
        """
        Получаем тело сайта
        :param content:
        :return:
        """
        new_content = ''
        in_body = False
        for line in str(content).split('\n'):
            if line.startswith('<body'):
                in_body = True
            elif line.startswith('</body>'):
                in_body = False
            else:
                if in_body:
                    new_content += line+'\n'
        return new_content

    @staticmethod
    def get_text_from_tag(tag, content):
        """
        Получаем текст из тэга
        :param tag:
        :param content:
        :return:
        """
        new_content = ''
        in_tag = False
        for line in str(content).split('\n'):
            if line.startswith('<{}>'.format(tag)):
                in_tag = True
            elif '</{}>'.format(tag) in line:
                new_content += line + '\n'
                in_tag = False
            elif line.startswith('<!-'):
                in_tag = False
            else:
                if in_tag:
                    new_content += line + '\n'
        return new_content

    def get_text_from_tags(self, tags, content):
        """
        Получаем текст по выбранным тэгам
        :param tags:
        :param content:
        :return:
        """
        for tag in tags:
            content = self.get_text_from_tag(tag, content)
        return content

    @staticmethod
    def cleartags(content, tags):
        """
        очищаем выбранные тэги
        :param content:
        :param tags:
        :return:
        """
        content = re.sub(r'<span.*?>', '', content).replace('</span>', '')
        for tag in tags:
            content = content.replace('{}'.format(tag), '')
        return content

    @staticmethod
    def find_links_and_replace(content):
        """
        Редактирование ссылок
        :param content:
        :return:
        """
        new_content = ''
        for line in content.split('\n'):
            if 'href=' in line:
                url = re.search(r'(href=\").*(\")', line)
                if url:
                    url = '["' + url.group(0) + ']'
                    url = url.replace('"href=', '')
                    line = re.sub(r'<a.*?>', url, line).replace('</a>', '')
                    new_content += line + '\n'
            else:
                new_content += line + '\n'
        return new_content

    def clear_and_prepare_text(self, content, tags):
        new_content = ''
        content = self.cleartags(content, tags)
        content = content.replace('\n', '')  # Убираем все переносы строки(делаем одну большую)
        for line in content.split('</p>'):
            new_content += '\t' + self.split_line_by_width(line, 75) + '\n\n'
        return new_content

    @staticmethod
    def split_line_by_width(text, maxlen):
        """
        Форматирование строки по ширине
        :param text:
        :param maxlen:
        :return:
        """
        new_text = ''  # записываем сюда новую строку
        c = 0  # счётчик символов с строке
        for i in text.split():  # проходим по каждому слову
            c += len(i)  # прибавляем длину слова
            if c >= maxlen:  # если символов больше максимума
                new_text += '\n'  # перенос строки
                c = len(i)  # счётчик равен первому слову в строке
            elif new_text != '':  # условие, чтобы не ставить пробел перед 1-м словом
                new_text += ' '  # ставим пробел после непоследнего слова в строке
                c += 1  # учитываем его в счётчике
            new_text += i  # прибавляем слово
        return new_text

    def get_content(self, url=None):
        """
        Проведение парсинга страницы и запись результата в файл
        :param url:
        :return:
        """
        html = self.settings_html.get_html(self.settings_html.get_response(url))
        if html:
            html = self.prepare_html(html)
            body = self.get_body(html)  # получаем тело страницы, для получения более полезной информации
            result_text = self.get_text_from_tags(['p'], body)  # получаем текст из выбранных тэгов
            result_text = self.find_links_and_replace(result_text)  # находим все ссылки в получившемся результате и
                                                                    # редактируем их
            result_text = self.clear_and_prepare_text(result_text, ['<br/>, </xml>', '</style>', '<br', '</a>'])  #очищаем текст от ненужных тэгов и
            # обрабатываем текст по ширине
            # записываем получившийся текст в файл
            try:
                with open(os.path.join(self.parse_url(url), 'result.txt'), 'w', encoding='utf-8') as fid:
                    fid.write(str(result_text))
            except IOError:
                print('Ошибка записи в файл')
            print('Парсинг страницы прошел успешно')
            return result_text

    @staticmethod
    def parse_url(url):
        if not url.endswith('/'):
            url += '/'
        parse_object = urlparse(url)
        path = parse_object.path
        result_path = BASE_dir + path
        # result_path = os.path.join(BASE_dir, path)
        try:
            os.makedirs(result_path)
        except OSError as e:
            print(e)
        return result_path

if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("Параметр url не введен")
    else:
        if len(sys.argv) > 3:
            print("Ошибка. Слишком много параметров.")
            sys.exit(1)
        if len(sys.argv) < 3:
            print("Ошибка. Слишком мало параметров.")
            sys.exit(1)

        param_name = sys.argv[1]
        param_value = sys.argv[2]

        if param_name == "-url" or param_name == "-u":
            parse_object = urlparse(param_value)
            if parse_object.path != '':
                html = SetupHtml()
                rw = ParseHtml(html, param_value)
        else:
            print("Ошибка. Неизвестный параметр '{}'".format(param_name))
            sys.exit(1)

