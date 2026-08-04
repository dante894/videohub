from app.config import MAX_VIDEO_HEIGHT


QUALITY_HEIGHTS = {
    "1080": 1080,
    "720": 720,
    "480": 480,
    "360": 360,
}


class OptionBuilder:

    @staticmethod
    def build(ctx, download_path, hook=None):

        height = min(
            QUALITY_HEIGHTS.get(ctx.quality, MAX_VIDEO_HEIGHT),
            MAX_VIDEO_HEIGHT,
        )

        opts = {

            "quiet": True,

            "merge_output_format": "mp4",

            "outtmpl": str(download_path / "%(title)s.%(ext)s"),

            "extractor_args": {

                "youtube": {

                    "player_client": list(dict.fromkeys([
                        ctx.player_client,
                        "android_vr",
                        "ios",
                        "mweb",
                    ]))

                }

            }

        }

        if hook:
            opts["progress_hooks"] = [hook]

        if ctx.cookiefile:
            opts["cookiefile"] = ctx.cookiefile

        if ctx.proxy:
            opts["proxy"] = ctx.proxy

        if ctx.audio:

            opts["format"] = "bestaudio/best"

            opts["postprocessors"] = [

                {

                    "key": "FFmpegExtractAudio",

                    "preferredcodec": "mp3",

                    "preferredquality": "192",

                }

            ]

        else:

            opts["format"] = (

                f"bestvideo[height<={height}]"

                "+bestaudio/"

                f"best[height<={height}]/"

                "bestvideo+bestaudio/best"

            )

        return opts