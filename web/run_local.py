"""Serve the UI and GEE API together using a credential file kept on this machine."""
import argparse
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def configure(args):
    credential=Path(args.credentials).expanduser().resolve()
    if not credential.is_file():raise ValueError('Không tìm thấy file JSON. Hãy kiểm tra đường dẫn file khóa trên máy bạn.')
    if credential.is_relative_to(ROOT):raise ValueError('Hãy giữ file khóa bên ngoài thư mục dự án để không đưa khóa lên GitHub hoặc web.')
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']=str(credential)
    os.environ['GEE_PROJECT_ID']=args.project
    os.environ['GEE_RICE_ASSET_ID']=args.asset

def main(argv=None):
    parser=argparse.ArgumentParser(description='Chạy Lúa Lab bằng file JSON xác thực GEE; không cần nhập API URL.')
    parser.add_argument('--credentials',required=True,help='Đường dẫn file JSON trên máy; không tải file lên web.')
    parser.add_argument('--project',default='du-lieu-ve-tinh-vietnam')
    parser.add_argument('--asset',default='projects/du-lieu-ve-tinh-vietnam/assets/rice_map_vietnam_2020')
    parser.add_argument('--port',type=int,default=8080)
    parser.add_argument('--check-gee',action='store_true',help='Kiểm tra xác thực và quyền đọc asset trước khi chạy web.')
    args=parser.parse_args(argv)
    if not 1<=args.port<=65535:parser.error('Port phải nằm trong 1–65535.')
    try:configure(args)
    except ValueError as e:parser.error(str(e))
    if args.check_gee:
        try:
            from web.api.gee_provider import GEEProvider
            provider=GEEProvider(args.project,args.asset)
            provider._initialize()
            import ee
            ee.data.getAsset(args.asset)
        except Exception as e:
            # Never print credential content or raw SDK error messages.
            parser.exit(1,f'Chưa xác thực hoặc đọc được asset ({type(e).__name__}). Kiểm tra file khóa, quyền service account và project Earth Engine.\n')
        print('Đã xác thực GEE và kiểm tra quyền đọc asset thành công.')
    print(f'Mở web tại http://127.0.0.1:{args.port}; giao diện tự kết nối GEE qua cùng máy chủ.')
    import uvicorn
    uvicorn.run('web.api.app:app',host='127.0.0.1',port=args.port)
if __name__=='__main__':main()
