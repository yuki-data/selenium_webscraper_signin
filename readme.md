# selenium login: seleniumでgoogle chromeを操作し会員制のサイトにログインしてスクリーンショットを保存する
## 機能
会員制サイトにログインしてから、スクリーンショットを取るwebスクレイピングツール。
ネットバンクやポイント交換サイトのマイページやなどで一定期間ごとに会員情報を自動でバックアップしたい場合に使えます。

AWS上で、cronのようなスケジューラーと組み合わせることで定期実行ごと自動化できます。

## 使い方

    from selenium_scraper.webscrape import Scraper
    scraper = Scraper(path_to_config="設定ファイルのパス")
    # landmark_elemend_idには、ログイン後のページに表示される何らかのhtml要素のidを指定する
    # その要素が見えたらスクリーンショットをとる
    scraper.get_screenshot(filename="保存するファイルの名前", path_to_directory="画像ファイル保存先のフォルダパス", landmark_elemend_id="#navigation-bar")

## 事前の準備
1. google chromeのインストール
2. chrome driverのダウンロード: [Downloads - ChromeDriver - WebDriver for Chrome](https://chromedriver.chromium.org/downloads)
3. seleniumのインストール: `pip install selenium`

## 設定ファイル
事前にログインページのパスワードやスクリーンショット画像の保存場所などを設定ファイルに記述しておく。
以下のような内容のconfig.ymlを作っておく。

    chrome:
        chromedriver_path: "chrome driverへのパス"
        profile_path: "chromeブラウザのプロファイル。デフォルトでいいなら空欄にする。"
    login:
        url: "ログインページのurl"
        selector:
            password: "ログインページでのパスワード入力欄のcssセレクタ"
            mail: "ログインページでのメールアドレス入力欄のcssセレクタ"
            signin: "ログインページでの送信ボタンのcssセレクタ"
    path:
        download:
            basics: "ダウンロードするフォルダのパス"
    secret:
        password: "ログインページで入力するパスワード"
        mail: "ログインページで入力するメールアドレレス"
    
