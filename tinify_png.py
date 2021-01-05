import tinify
import os
from datetime import datetime
# @ 使用熊猫压缩图片 https://tinypng.com/
# modified by xy 2020-12-08 修改输出文件名
# modified by xy 2020-12-31 改为从文件夹里转换多个图片

'''
pip install --upgrade tinify
'''

version_ = '1.3'
key = "your key"
def check_api(api_key):
    '''校验api有效性'''
    try:
      tinify.key = api_key
      tinify.validate()
    except tinify.Error as e:
      # Validation of API key failed.
      pass

def comress_img(source_file):
    '''压缩图片'''
    try:
      # Use the Tinify API client.
        source = tinify.from_file(source_file)
        now_time = str(datetime.now().strftime('%H%M%S'))
        output_file = os.path.join(os.path.dirname(source_file), \
            (now_time + '_' + os.path.basename(source_file)))
        source.to_file(output_file)
        print('已压缩', output_file)
        print('本月已使用', tinify.compression_count, '次,', '共500次。')
    except tinify.AccountError as e:
      print("The error message is: %s" % (e.message))
      # Verify your API key and account limit.
    except tinify.ClientError as e:
      # Check your source image and request options.
      pass
    except tinify.ServerError as e:
      # Temporary issue with the Tinify API.
      pass
    except tinify.ConnectionError as e:
      # A network connection error occurred.
      pass
    except Exception as e:
      # Something else went wrong, unrelated to the Tinify API.
      pass

if __name__ == "__main__":
    check_api(key)
    antwort = input('是否保留原始图片(yes/no): ')
    for root, dirs, files in os.walk('/home/mount_mac/test/35'):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for f_path in files:
            r_path = os.path.join(root, f_path)
            comress_img(r_path)
            if antwort == 'no' or antwort == 'NO' or antwort == 'n' or antwort == 'N':
                os.remove(r_path)