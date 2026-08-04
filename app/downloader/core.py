from yt_dlp import YoutubeDL


class DownloaderCore:

    @staticmethod
    def download(url, options):

        with YoutubeDL(options) as ydl:

            info = ydl.extract_info(
                url,
                download=True,
            )

            filename = ydl.prepare_filename(info)

        return filename, info