# -*- coding: utf-8 -*-
# @Author: Yining Qin
# @Date:   2020-09-26 00:00:00
# @Loaction: Livermoer


import os
import time
import re
import logging
import urllib.request
import urllib.error
from urllib.parse import quote

from multiprocessing import Pool
from user_agent import generate_user_agent


log_file = 'Images_d.log'
logging.basicConfig(level=logging.DEBUG, filename=log_file, filemode="a+", format="%(asctime)-15s %(levelname)-8s  %(message)s")


def download_page(url):
    """download raw content of the page
    
    Args:
        url (str): url of the page 
    
    Returns:
        raw content of the page
    """
    try:
        headers = {}
        headers['User-Agent'] = generate_user_agent()
        headers['Referer'] = 'https://www.google.com'
        req = urllib.request.Request(url, headers = headers)
        resp = urllib.request.urlopen(req)
        return str(resp.read())
    except Exception as e:
        print('Downloading error at {0}'.format(url))
        logging.error('Downloading error at {0}'.format(url))
        return None


def parse_page(url):
    """parge the page and get all the links of images, max number is 100 due to limit by google
    
    Args:
        url (str): url of the page
    
    Returns:
        A set containing the urls of images
    """
    page_content = download_page(url)
    if page_content:
        link_list = re.findall('src="(.*?)"', page_content)
        if len(link_list) == 0:
            print('get 0 links from page {0}'.format(url))
            logging.info('get 0 links from page {0}'.format(url))
            return set()
        else:
            return set(link_list)
    else:
        return set()


def download_images(main_keyword, supplemented_keywords, download_dir):
    """download images with one main keyword and multiple supplemented keywords
    
    Args:
        main_keyword (str): main keyword
        supplemented_keywords (list[str]): list of supplemented keywords
    
    Returns:
        None
    """  
    image_links = set()
    print('Process {0} Main keyword: {1}'.format(os.getpid(), main_keyword))

    # create a directory for a main keyword
    img_dir =  download_dir + main_keyword + '/'
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    for j in range(len(supplemented_keywords)):
        print('Process {0} supplemented keyword: {1}'.format(os.getpid(), supplemented_keywords[j]))
        search_query = quote(main_keyword + ' ' + supplemented_keywords[j])
        url = 'https://www.google.com/search?q=' + search_query + '&source=lnms&tbm=isch'
        image_links = image_links.union(parse_page(url))
        print('Process {0} get {1} links so far'.format(os.getpid(), len(image_links)))
        print(image_links)
        time.sleep(1)
    print ("Process {0} get totally {1} links".format(os.getpid(), len(image_links)))
    
    print ("........................................................................")
    print ("...Start downloading....................................................")
    count = 1
    for link in image_links:
        try:
            req = urllib.request.Request(link, headers = {"User-Agent": generate_user_agent()})
            response = urllib.request.urlopen(req)
            data = response.read()
            file_path = img_dir + '{0}.jpg'.format(count)
            with open(file_path,'wb') as wf:
                wf.write(data)
            print('Process {0} fininsh image {1}/{2}.jpg'.format(os.getpid(), main_keyword, count))
            count += 1
        except urllib.error.URLError as e:
            logging.error('URLError while downloading image {0}\nreason:{1}'.format(link, e.reason))
            continue
        except urllib.error.HTTPError as e:
            logging.error('HTTPError while downloading image {0}\nhttp code {1}, reason:{2}'.format(link, e.code, e.reason))
            continue
        except Exception as e:
            logging.error('Unexpeted error while downloading image {0}\nerror type:{1}, args:{2}'.format(link, type(e), e.args))
            continue

    print("Finish downloading, total {0} errors".format(len(image_links) - count))
    


if __name__ == '__main__':
    main_keywords = ['solar', 'wind', 'energy storage']
    supplemented_keywords = ['commercial','residential']
   
    download_dir = './data/'

    # download with single process
    # for i in range(len(main_keywords)):
    #     download_images(main_keywords[i], supplemented_keywords, download_dir)


    # download with multiple process
    p = Pool() # number of process is the number of cores of your CPU
    for i in range(len(main_keywords)):
        p.apply_async(download_images, args=(main_keywords[i], supplemented_keywords, download_dir))
    p.close()
    p.join()
    print('All fininshed')

