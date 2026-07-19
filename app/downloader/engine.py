
import shutil
from pathlib import Path
from yt_dlp import YoutubeDL
from app.core.logger import logger
from app.config import MAX_VIDEO_HEIGHT,YTDLP_COOKIES_FILE,YTDLP_PROXY,YTDLP_PROXY_AR,YTDLP_PROXY_US,YTDLP_PROXY_EU
QUALITY_HEIGHTS={"1080":1080,"720":720,"480":480,"360":360}
_WRITABLE_COOKIES_PATH=Path("/tmp/videohub_cookies.txt")
PROXIES=[("DEFAULT",YTDLP_PROXY),("AR",YTDLP_PROXY_AR),("US",YTDLP_PROXY_US),("EU",YTDLP_PROXY_EU)]
class VideoDownloader:
    def __init__(self,download_path="downloads"):
        self.download_path=Path(download_path); self.download_path.mkdir(exist_ok=True)
        self.cookies_file=self._prepare_cookies_file()
    def _prepare_cookies_file(self):
        if not YTDLP_COOKIES_FILE: return None
        src=Path(YTDLP_COOKIES_FILE)
        if not src.exists(): return None
        try:
            shutil.copyfile(src,_WRITABLE_COOKIES_PATH); return str(_WRITABLE_COOKIES_PATH)
        except Exception:
            return str(src)
    def _anti_bot_options(self,proxy=None):
        o={"extractor_args":{"youtube":{"player_client":["android","web","ios"]}}}
        if self.cookies_file:o["cookiefile"]=self.cookies_file
        if proxy:o["proxy"]=proxy
        return o
    def _download_with_proxy(self,options,url):
        last=None
        for region,proxy in PROXIES:
            if not proxy: continue
            try:
                opts=options.copy(); opts.update(self._anti_bot_options(proxy))
                with YoutubeDL(opts) as ydl:
                    info=ydl.extract_info(url,download=True); return ydl.prepare_filename(info),info
            except Exception as e:
                last=e
        raise last
    def get_info(self,url):
        with YoutubeDL({"quiet":True,"skip_download":True,**self._anti_bot_options()}) as ydl:
            i=ydl.extract_info(url,download=False)
        return {"title":i.get("title"),"duration":i.get("duration"),"thumbnail":i.get("thumbnail"),"uploader":i.get("uploader"),"webpage_url":i.get("webpage_url")}
    def download(self,url,quality="1080",audio=False,progress_callback=None):
        def hook(d):
            if progress_callback: progress_callback(d)
        h=min(QUALITY_HEIGHTS.get(str(quality),MAX_VIDEO_HEIGHT),MAX_VIDEO_HEIGHT)
        opts={"outtmpl":str(self.download_path/"%(title)s.%(ext)s"),"progress_hooks":[hook],"quiet":True,**self._anti_bot_options()}
        if audio:
            opts["format"]="bestaudio/best"; opts["postprocessors"]=[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]
        else:
            opts["format"]=f"bestvideo[height<={h}]+bestaudio/best[height<={h}]/bestvideo+bestaudio/best"; opts["merge_output_format"]="mp4"
        try:
            with YoutubeDL(opts) as ydl:
                info=ydl.extract_info(url,download=True); fn=ydl.prepare_filename(info)
        except Exception as e:
            t=str(e).lower()
            if any(x in t for x in ["country","geo","blocked","403","unavailable"]):
                fn,info=self._download_with_proxy(opts,url)
            else: raise
        if audio: fn=str(Path(fn).with_suffix(".mp3"))
        return fn
