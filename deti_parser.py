import requests
import csv
import dataclasses
from datetime import date
from bs4 import BeautifulSoup

@dataclasses.dataclass
class Child:
    id: str
    age: int
    name: str
    gender: str
    region: str
    healthGroup: int
    isSibling: bool
    character: str
    mother: str
    father: str
    form: int
    link: str
    myNotes: str
    verdict: int

def VerdictToString(v: int)->str:
    if v==0:
        return 'не решено'
    if v==1:
        return 'наш отказ'
    if v==2:
        return 'опеки отказ'
    if v==3:
        return 'попробовать позже'
    if v==4:
        return 'надо попробовать'
    return '?'

def FormToString(v: int)->str:
    if v==1:
        return 'опека, попечительство'
    if v==2:
        return 'усыновление'
    if v==3:
        return 'усыновление, опека, попечительство'
    return '?'

def ParseHealthGroup(s: str) -> int:
    if len(s)>0:
        if s[0] in ['1','2','3','4','5']: 
            return int(s[0])
    return 0

def ParseForm(s: str) -> int:
    result = 0
    if s.find('пека') != -1:
        result += 1
    if s.find('сыновление') != -1:
        result += 2
    
    return result

def ConvertRowUsynoviteRFToChild(row: dict) -> Child:
    child = Child
    child.id = row['id']
    child.age = int(row['age'])
    child.name = row['name']
    child.gender = str(row['gender'][0])
    child.region = row['region']
    child.healthGroup = ParseHealthGroup(row['healthGroup'])
    child.isSibling = row['isSibling'] in ['есть','Есть','ЕСТЬ','есть+','Есть+','ЕСТЬ+']
    child.character = row['character']
    child.mother = row['motherLack']
    child.father = row['fatherLack']
    child.form = ParseForm(row['custodyForm'])
    child.link = 'https://xn--b1agisfqlc7e.xn--p1ai/children/{}'.format(child.id)
    child.myNotes = ''
    child.verdict = 0
    return child

def ConvertChildToDict(child: Child) -> dict:
    result = {}
    result['id'] = child.id
    result['age'] = child.age
    result['name'] = child.name
    result['gender'] = child.gender
    result['region'] = child.region
    result['healthGroup'] = child.healthGroup
    result['isSibling'] = child.isSibling
    result['character'] = child.character
    result['mother'] = child.mother
    result['father'] = child.father
    result['form'] = child.form
    result['link'] = child.link
    result['myNotes'] = child.myNotes
    result['verdict'] = child.verdict
    return result

def ParseUsynovyteRF(children: dict):
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})
    resp = session.get('https://xn--b1agisfqlc7e.xn--p1ai/')

    page = 1
    pages = 999

    while page <= pages:
        resp = session.get('https://xn--b1agisfqlc7e.xn--p1ai/api/children/cv?page={}&limit=100&genderId=2&ageFrom=0&ageTo=3'.format(page))
        respData = resp.json()
        for row in respData['data']:
            child = ConvertRowUsynoviteRFToChild(row)
            children[Child.id] = {'dict': ConvertChildToDict(child),
                                  'child': child}
        pages = int(respData['totalPages'])
        page+=1

    return children

def ParseAge(s: str) -> int:
    s=s.lower()
    m=0
    y=0
    if s.find('январь'):
        m=1
    if s.find('февраль'):
        m=2
    if s.find('март'):
        m=3
    if s.find('апрель'):
        m=4
    if s.find('май'):
        m=5
    if s.find('июнь'):
        m=6
    if s.find('июль'):
        m=7
    if s.find('август'):
        m=8
    if s.find('сентябрь'):
        m=9
    if s.find('октябрь'):
        m=10
    if s.find('ноябрь'):
        m=11
    if s.find('декабрь'):
        m=12
    year_str = ''
    for c in s:
        if c >= '0' and c <='9':
            year_str+=c
    y=int(year_str)

    today = date.today()
    bornDate = date(y,m,28)
    age = today-bornDate
    return int(age.days/365)+1

def ConvertSirotaSpbToChild(soup: BeautifulSoup, id: str):
    child = Child
    data = soup.find('span', class_='infoname')
    child.name = data.decode_contents()
    data = soup.find('datetime')
    child.age = ParseAge(data.decode_contents())
    data = soup.findAll('span', class_='infodata')
    d = data.pop()
    d = data.pop()
    d = data.pop()
    child.gender = d.decode_contents()[0]
    d = data.pop()
    child.form = ParseForm(d.decode_contents())
    d = data.pop()
    child.father = d.decode_contents()
    d = data.pop()
    child.mother = d.decode_contents()
    d = data.pop()
    child.healthGroup = ParseHealthGroup(d.decode_contents())
    d = data.pop()
    child.character = d.decode_contents()

    data = soup.findAll('p', class_='h1add')
    for d in data:
        is_addr = d.find('em')
        if is_addr:
            child.region = d.decode_contents()[16:].split(',')[0]

    data = soup.findAll('div', class_='form-control mt10')
    for d in data:
        content = d.decode_contents()
        is_sibling = content.find('Имеет несовершеннолетних родственников')
        child.isSibling = (is_sibling>=0)

    child.id = id
    child.link = 'http://sirota-spb.ru/bd/childrenbase/?sex=2&month=&year=&hair=&eyes=&possibleSettleForm=&minAge=1&maxAge=3&key={}'.format(id)
    child.myNotes = ''
    child.verdict = 0
    return child

def contains(id: str, ids: list):
    for i in ids:
        if id == i:
            return True
    return False

def ParseSirotaSpbRF(children: dict):
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})
    resp = session.get('http://sirota-spb.ru/bd/childrenbase/?sex=2&month=&year=&hair=&eyes=&possibleSettleForm=&minAge=1&maxAge=3')

    html = resp.text

    ids = list()

    soup = BeautifulSoup(html, 'html.parser')
    raw_ids = soup.findAll('a',class_='normal')
    for i in raw_ids:
        ids.append(i.get_attribute_list('href')[0][91:])

    i: int
    i=0

    while i < len(ids):
        resp = session.get('http://sirota-spb.ru/bd/childrenbase/?sex=2&month=&year=&hair=&eyes=&possibleSettleForm=&minAge=1&maxAge=3&key={}'.format(ids[i]))
        html = resp.text
        soup = BeautifulSoup(html, 'html.parser')
        id = ids[i]
        child = ConvertSirotaSpbToChild(soup, id)
        raw_ids = soup.findAll('a',class_='normal')
        for item in raw_ids:
            new_id = item.get_attribute_list('href')[0][91:]
            if not contains(new_id, ids):
                ids.append(new_id)

        children[id] = {'dict': ConvertChildToDict(child),
                        'child': child}
        i = i + 1

    return children

def merge(d1: dict, d2: dict) -> dict:

    flag = False
    diff = ''

    if int(d1['age']) != int(d2['age']):
        diff += ' age: {}->{}'.format(d1['age'],d2['age'])
        d1['age'] = d2['age']
        flag = True
    if d1['name'] != d2['name']:
        diff += ' name: {}->{}'.format(d1['name'],d2['name'])
        d1['name'] = d2['name']
        flag = True
    if d1['gender'] != d2['gender']:
        diff += ' gender: {}->{}'.format(d1['gender'],d2['gender'])
        d1['gender'] = d2['gender']
        flag = True
    if d1['region'] != d2['region']:
        diff += ' region: {}->{}'.format(d1['region'],d2['region'])
        d1['region'] = d2['region']
        flag = True
    if int(d1['healthGroup']) != int(d2['healthGroup']):
        diff += ' healthGroup: {}->{}'.format(d1['healthGroup'],d2['healthGroup'])
        d1['healthGroup'] = d2['healthGroup']
        flag = True
    if d1['isSibling'] != str(d2['isSibling']):
        diff += ' isSibling: {}->{}'.format(d1['isSibling'],d2['isSibling'])
        d1['isSibling'] = d2['isSibling']
        flag = True
    if d1['character'] != d2['character']:
        diff += ' character: {}->{}'.format(d1['character'],d2['character'])
        d1['character'] = d2['character']
        flag = True
    if d1['mother'] != d2['mother']:
        diff += ' mother: {}->{}'.format(d1['mother'],d2['mother'])
        d1['mother'] = d2['mother']
        flag = True
    if d1['father'] != d2['father']:
        diff += ' father: {}->{}'.format(d1['father'],d2['father'])
        d1['father'] = d2['father']
        flag = True
    if int(d1['form']) != int(d2['form']):
        diff += ' form: {}->{}'.format(d1['form'],d2['form'])
        d1['form'] = d2['form']
        flag = True
    if d1['link'] != d2['link']:
        diff += ' link: {}->{}'.format(d1['link'],d2['link'])
        d1['link'] = d2['link']
        flag = True

    index = d1['myNotes'].find(' обновлены данные:')

    if (index>=0):
        print(d1['myNotes'])
        print(index)
        d1['myNotes'] = d1['myNotes'][:index]
        print(d1['myNotes'])
        print('=====================')

    if flag:
        d1['myNotes'] += ' обновлены данные: '+diff

    return d1

def main():
    children = {}
    
    children = ParseSirotaSpbRF(children)
    children = ParseUsynovyteRF(children)

    newChildren = {}

    with open('childrenNew.csv') as f:
        reader = csv.DictReader(f)
        for row in reader:
            newChildren[row['id']] = row

    for d in children:
        if d in newChildren:
            newChildren[d] = merge(newChildren[d],children[d]['dict'])
        else:
            newChildren[d]= children[d]['dict']
            newChildren[d]['verdict'] = VerdictToString(int(newChildren[d]['verdict']))
            newChildren[d]['myNotes'] = 'новая анкета'

    with open('childrenNew.csv', 'w') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=list(list(newChildren.values())[0].keys()),
        )
        writer.writeheader()
        for d in children:
            writer.writerow(newChildren[d])

if __name__ == "__main__":
    main()
