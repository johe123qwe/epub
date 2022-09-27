from googleapiclient.discovery import build
from google.oauth2 import service_account
from datetime import datetime
import re
import os
import shutil
import zipfile
import click
from pathlib import Path


# 一个替换的库https://github.com/MisterL2/python-util

# 读取谷歌工作表内容，批量发送 skype 信息

version = 'v1.1'
'''
v1.1 20220927 改用 pathlib 获取路径中的文件夹名 Path.parts, 修复了诸多内容
v1.0 20220926 第一版本
'''
print('修改中文书籍小工具 {} \n'.format(version))



SERVICE_ACCOUNT_FILE = 'token.json' # 谷歌 API 服务器账号密钥
SCOPES = ['https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets']

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()
sheet_id = '116Drg5MqwoF5bcmxzuc6vG0279AcqYX5NRKwoWTfeos'

# 获取工作表名
# try:
#     print('正在获取工作表 {} 内容'.format(sheet_id))
#     sheet_metadata = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
#     sheets = sheet_metadata.get('sheets', '')
# except Exception as e:
#     print('读取工作表 {} 失败,请检查. {}'.format(sheet_id, e))

def get_sheet_data(sheet_range, sheet_id) :
    ''' 获取表格数据 '''
    name_range = sheet_range + '!A2:B'
    result = sheet.values().get(spreadsheetId = sheet_id,
                        range = name_range).execute()
    info_data = result.get('values', [])
    # print(36, info_data)
    return info_data



def upload_data(result, sheet_range, update_sheet_id) :
    ''' 上传数据 '''
    body = {
        'values': result
    }

    # 使用 update 参数写入数据
    sheet.values().update(
        spreadsheetId=update_sheet_id, range=sheet_range,
        valueInputOption='USER_ENTERED', body=body).execute()

def gen_dic(content) :
    ''' 替换前后内容生成字典 '''
    print('共 {} 处改点'.format(len(content)))
    replace_dic = {}
    for index in range(len(content)) :
        # print(content[index][0], content[index][1])
        before = content[index][0].strip('')
        after = content[index][1].strip('')
        replace_dic[before] = after
    return replace_dic




# 删除用于解压的临时目录
def delete_path(tmp_path):
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)

def creat_tmp_dir(main_epub):
    ''' 创建临时文件夹 '''
    path = os.path.dirname(main_epub)
    tmp_path = os.path.join(path, '_tmp_')
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    else:
        shutil.rmtree(tmp_path)
    return tmp_path

def filereplace(filename, patternToReplace, replacementString, out=None, regex=False, encoding=None):
    with open(filename, 'r+', encoding=encoding) as f:
        file_content = f.read()
        if regex:
            from re import sub
            new_content = sub(patternToReplace,replacementString,file_content)
        else:
            new_content = file_content.replace(patternToReplace,replacementString)
        if out is None:
            f.seek(0)
            f.truncate(0)
            f.write(new_content)
        else:
            with open(out, 'w', encoding=encoding) as out_file:
                out_file.write(new_content) # Opening as 'w' means I overwrite all content in that file
        if patternToReplace in file_content:
            return 1, filename
        else:
            return 0,
# 删除用于解压的临时目录
def delete_path(tmp_path):
    if os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)

def get_files(dir_path):
    ''' 获取文件路径 '''
    names = os.listdir(dir_path)
    section_files = [i for i in names if i.startswith('Section')]
    return section_files

# 解压 EPUB 并替换
def extract(epub_file, r_dic):
    tmp_path = creat_tmp_dir(epub_file)
    path = os.path.dirname(epub_file)
    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)
    if zipfile.is_zipfile(epub_file):
        os.chdir(path)
        if epub_file.endswith(".epub"):
            fz = zipfile.ZipFile(epub_file, 'r')
            extr_path = os.path.join(tmp_path, os.path.basename(epub_file).split('.epub')[0])
            for e_file in fz.namelist():
                fz.extract(e_file, extr_path)
            fz.close()

            files = get_files(os.path.join(extr_path, 'OEBPS', 'Text'))
            os.chdir(os.path.join(extr_path, 'OEBPS', 'Text'))
            upload_data = []
            for k,v in r_dic.items():
                ''' 替换内容 '''
                count_num_ = 0
                replace_files = []
                row = []
                for file_path in files:
                    now = datetime.now()
                    result = filereplace(file_path, k, v, regex=True)
                    count_num_ += result[0]
                    if result[0] > 0:
                        replace_files.append(result[1])
                if count_num_ == 0:
                    info = '{} 未找到请检查'.format(now)
                else:
                    info = '{} 已替换 {} 处'.format(now, count_num_)
                row.append(info)
                row.append(', '.join(replace_files))
                upload_data.append(row)
            return extr_path, upload_data

    else:
        print(epub_file, '不是压缩文件或不存在')
        delete_path(tmp_path)
        os._exit(0)


# 打包新的EPUB
def dabao(epub_file, tmp_path):
    old_epub = os.path.basename(epub_file)
    now_time = str(datetime.now().strftime('%Y%m%d%H'))
    new_xuanbian = re.sub('(\d{4,})', now_time, old_epub)
    new_epub = os.path.join(os.path.dirname(epub_file), new_xuanbian)
    z = zipfile.ZipFile(new_epub, 'w')
    os.chdir(tmp_path)
    for root, _, files in os.walk('.'):
        for f in files:
            n_files = os.path.join(root, f)
            z.write(n_files, compress_type=zipfile.ZIP_DEFLATED)
    z.close()
    # 退出目录，否则在win上执行delete_path函数时报另一个进程占用，无法访问。
    # os.chdir(path)
    print('\n已生成', new_epub)

def fileread(source):
    with open(source, "r", encoding="utf-8") as src: 
        file_content = src.read()
        return file_content

def fileoverwrite(filename, thing, encoding='gbk'):
    a = open(filename, 'w', encoding=encoding)
    a.write(str(thing))
    a.close()

def list_file(path):
    ''' 转换文件 '''
    fname = []
    for root, d_names, f_names in os.walk(path):
        for f in f_names:
            fname.append(os.path.join(root, f))
    # print(fname)
    return fname

def replace_text(dst_dir, r_dic):
    files = list_file(dst_dir)
    upload_data = []
    for k,v in r_dic.items():
        ''' 替换内容 '''
        count_num_ = 0
        replace_files = []
        row = []
        for file_path in files:
            now = datetime.now()
            # print(211, file_path)
            result = filereplace(file_path, k, v, regex=True, encoding='utf-8')
            count_num_ += result[0]
            if result[0] > 0:
                replace_files.append(result[1])
        if count_num_ == 0:
            info = '{} 未找到请检查'.format(now)
        else:
            info = '{} 已替换 {} 处'.format(now, count_num_)
        row.append(info)
        row.append(', '.join(replace_files))
        upload_data.append(row)
    return upload_data

@click.command()
@click.option('-e', '--epubfile', type=str, help='添加EPUB文件')
@click.option('-t', '--textdir', type=str, help='添加text文件夹')
@click.option('-s', '--sheetname', type=str, help='谷歌表格sheet名')
def main(epubfile, textdir, sheetname):
    replace_content = get_sheet_data(sheetname, sheet_id)
    r_dic = gen_dic(replace_content)
    extr_path = extract(epubfile, r_dic)[0]
    sheet_range = sheetname + '!C2'
    upload_data(extract(epubfile, r_dic)[1], sheet_range, sheet_id)
    dabao(epubfile, extr_path)
    delete_path(creat_tmp_dir(epubfile))


    if textdir is not None:
        # 替换 txt 版本
        sheet_range_ = sheetname + '!E2'
        upload_data(replace_text(textdir, r_dic), sheet_range_, sheet_id)
        print('已替换 txt 版本')

        # 转换成 gbk 版本
        new_name = Path(textdir).parts[-1] + '_gbk'
        dst_dir = os.path.join(Path(textdir).parent, new_name)
        if os.path.exists(dst_dir):
            shutil.rmtree(dst_dir)

        shutil.copytree(textdir, dst_dir)
        files = list_file(dst_dir)
        for file in files:
            # print(219, file)
            fileoverwrite(file, fileread(file), encoding='gbk')
        print('已生成gbk格式的txt', new_name)
    else:
        print('未指定txt, 未转换')
if __name__ == '__main__':
    main()