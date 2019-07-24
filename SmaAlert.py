from os import remove
import requests
import json
import pandas as pd
import smtplib
from Config import config
from matplotlib import pyplot as plt

from jinja2 import Environment, FileSystemLoader
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

c = config('settings.conf')


def download_data(ticker):
    print (ticker)
    url = 'https://financialmodelingprep.com/api/v3/historical-price-full/%s' % (ticker)
    response = requests.get(url)
    data = json.loads(response.text)['historical']
    dataframe_li = []
    for d in data:
        temp = [d['open'], d['high'], d['low'], d['close'], d['date']]
        dataframe_li.append(temp)

    df = pd.DataFrame(dataframe_li, columns=['open', 'high', 'low', 'close', 'date'])
    return df


def save_plot(filename, data, time_frame=-1):
    
    data['200SMA'] = data['close'].rolling(window=c.get_setting('slow_sma')).mean()
    data['20SMA'] = data['close'].rolling(window=c.get_setting('fast_sma')).mean()

    if time_frame != -1:
        data = data.tail(time_frame)
        data.reset_index(inplace=True, drop=True)
    
    plt.figure(figsize=(10,8))
    plt.plot(data['close'], color='blue')
    plt.plot(data['200SMA'], color='orange')
    plt.plot(data['20SMA'], color='green')
    plt.savefig(filename + '.png')


def precent_change(new, old):
    return round(((new - old) / old) * 100, 2)


def get_style_string():
    with open(c.get_setting('css_path'), 'r') as file:
        return file.read()


class stock_data():
    def __init__(self):
        self.src = ''
        self.data = ''


class html_email():
    def __init__(self):
        self.info = []
        self.graph_index = 0

    def add_stock(self, ticker, time_frame=-1):
        temp = stock_data()
        data = download_data(ticker)
        data['200SMA'] = data['close'].rolling(window=200).mean()
        data['20SMA'] = data['close'].rolling(window=20).mean()

        plot_data = data
        if time_frame != -1:
            plot_data = plot_data.tail(time_frame)
            plot_data.reset_index(inplace=True, drop=True)

        plt.title(ticker)
        line_width = 0.85
        plt.plot(plot_data['close'], color='blue', linewidth=line_width)
        plt.plot(plot_data['200SMA'], color='orange', linewidth=line_width)
        plt.plot(plot_data['20SMA'], color='green', linewidth=line_width)
        plt.savefig(str(self.graph_index) + '.png', bbox_inches='tight')
        plt.clf()

        temp.src = str(self.graph_index) + '.png'
        self.graph_index += 1

        avg_volatility = data['close'].diff().std()

        msg = ''
        msg += '<tr><td>Price: $' + str(data['close'].iloc[-1]) + '\n</td></tr>'
        msg += '<td>Todays Change: ' + str(precent_change(data.iloc[-1]['close'], data.iloc[-2]['close'])) + '%\n</td></tr>'

        msg += '<tr><td>7 Day \tChange: ' + str(precent_change(data.iloc[-1]['close'], data.iloc[-5]['close'])) + '% '
        msg += 'Volatility: ' + str(round(data.iloc[-5:]['close'].diff().std()/avg_volatility, 2)) + '\n</td></tr>'

        msg += '<tr><td>1 Month Change: ' + str(precent_change(data.iloc[-1]['close'], data.iloc[-20]['close'])) + '% '
        msg += 'Volatility: ' + str(round(data.iloc[-20:]['close'].diff().std()/avg_volatility, 2)) + '\n</td></tr>'

        msg += '<tr><td>6 Month Change: ' + str(precent_change(data.iloc[-1]['close'], data.iloc[-20 * 6]['close'])) + '% '
        msg += 'Volatility: ' + str(round(data.iloc[-20 * 6:]['close'].diff().std()/avg_volatility, 2)) + '\n</td></tr>'

        msg += '<tr><td>1 Year \tChange: ' + str(precent_change(data.iloc[-1]['close'], data.iloc[-251]['close'])) + '% '
        msg += 'Volatility: ' + str(round(data.iloc[-251:]['close'].diff().std()/avg_volatility, 2)) + '\n</td></tr>'

        temp.data = msg

        self.info.append(temp)


    def send_email(self, to_address, from_address):
        env = Environment(loader=FileSystemLoader('.'))
        template = env.get_template(c.get_setting('html_path'))

        html_out = template.render(
            graphs=self.info,
            style=get_style_string()
        )

        #print(html_out)

        msg = MIMEMultipart()
        msg["To"] = to_address
        msg["From"] = from_address
        msg["Subject"] = "alert"

        msgText = MIMEText(html_out, 'html')
        msg.attach(msgText)

        for d in self.info:
            fp = open(d.src, 'rb')                                                    
            img = MIMEImage(fp.read())
            fp.close()
            img.add_header('Content-ID', '<{}>'.format(d.src))
            msg.attach(img)

        email = c.get_setting("email_address")
        password = c.get_setting("email_password")

        server = smtplib.SMTP(c.get_setting("smtp_server"))
        server.starttls()
        server.login(email, password)
        problems = server.send_message(msg)
        server.quit()
        return problems


    def clean(self):
        for f in self.info:
            remove(f.src)

look_back = int(c.get_setting('chart_length'))

with open(c.get_setting('symbols')) as file:
    temp = html_email()
    for line in file:
        if len(line) > 1:
            if line[-1] == '\n':
                line = line[:-1]
            temp.add_stock(line, look_back)

    print(temp.send_email(c.get_setting("email_recipients"), c.get_setting("email_address")))
    temp.clean()