from db import settings
from db import db
import datetime
import logging

logging.basicConfig(level=logging.INFO,
                    format='[%(asctime)s] %(levelname)s @ %(name)s: %(message)s')
logger = logging.getLogger(__name__)

coll = db['author']  # 获得collection的句柄
logger.info('开始计算粉丝增速')
for each_author in coll.find().batch_size(8):
    rate = []
    i = 0
    # 数据量小于等于2条
    if ('data' not in each_author or len(each_author['data']) < (i + 2)):
        continue
    if ('fansRate' in each_author and len(each_author['fansRate']) >= 1):
        lastest_date = each_author['fansRate'][0]['datetime']

    def getDate(date):
        return date - datetime.timedelta(
            hours=date.hour,
            seconds=date.second,
            microseconds=date.microsecond,
            minutes=date.minute)

    def next_c(i):
        return each_author['data'][i]['fans'], each_author['data'][i][
            'datetime'], each_author['data'][i][
                'datetime'] - datetime.timedelta(
                    hours=each_author['data'][i]['datetime'].hour,
                    seconds=each_author['data'][i]['datetime'].second,
                    microseconds=each_author['data'][i]['datetime'].
                    microsecond,
                    minutes=each_author['data'][i]['datetime'].minute)

    c_fans, c_datetime, c_date = next_c(i)

    def next_p(i):
        return each_author['data'][i + 1]['fans'], each_author['data'][
            i + 1]['datetime'], each_author['data'][
                i + 1]['datetime'] - datetime.timedelta(
                    hours=each_author['data'][i + 1]['datetime'].hour,
                    seconds=each_author['data'][i + 1]['datetime'].second,
                    microseconds=each_author['data'][i + 1]['datetime'].
                    microsecond,
                    minutes=each_author['data'][i + 1]['datetime'].minute)

    p_fans, p_datetime, p_date = next_p(i)

    # 相差粉丝数
    delta_fans = c_fans - p_fans
    # 相差日期数
    days = c_datetime.day - p_datetime.day
    # 相差秒数
    seconds = days + (c_datetime.second - p_datetime.second)

    while i < len(each_author['data']) - 2:

        # 已经有了该日期的数据
        if 'fansRate' in each_author and c_date <= lastest_date:
            break

        # 是同一天
        if c_datetime.day == p_datetime.day:
            i += 1
            p_fans, p_datetime, p_date = next_p(i)
            continue

        # 相差一天
        if (c_date - p_date).days == 1:
            delta_fans = c_fans - p_fans
            seconds = days + (c_datetime.second - p_datetime.second)
            rate.append({
                'rate':
                int(delta_fans / (1 + seconds / (60 * 60 * 24))),
                'datetime':
                c_date
            })
            i += 1
            c_fans, c_datetime, c_date = next_c(i)
            p_fans, p_datetime, p_date = next_p(i)
            delta_fans = c_fans - p_fans
            seconds = days + (c_datetime.second - p_datetime.second)
            continue

        # 相差多天
        days = (c_date - p_date).days
        while days > 1:
            t_rate = delta_fans / (days + seconds / (60 * 60 * 24))
            t_date = c_date - datetime.timedelta(1)
            t_fans = c_fans - t_rate
            delta_fans = c_fans - t_fans
            rate.append({
                'rate':
                int(delta_fans / (1 + seconds / (60 * 60 * 24))),
                'datetime':
                c_date
            })
            c_fans = t_fans
            c_date = t_date
            days -= 1
    coll.update_one({
        'mid': each_author['mid']
    }, {'$push': {
        'fansRate': {
            '$each': rate,
            '$position': 0
        }
    }}, True)
    if len(rate) != 0:
        coll.update_one({
            'mid': each_author['mid']
        }, {'$set': {
            'cRate': rate[0]['rate']
        }}, True)
    pass
