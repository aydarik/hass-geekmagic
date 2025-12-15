"""Constants for the Geek Magic integration."""

DOMAIN = "geek_magic"
CONF_IP_ADDRESS = "ip_address"
DEFAULT_NAME = "Geek Magic"

CONF_RENDER_URL = "render_url"
CONF_HTML_TEMPLATE = "html_template"

DEFAULT_HTML_TEMPLATE = """<html lang='en'>
<head>
    <title>GeekMagic</title>
    <style>
        body {
            margin: 0;
            background: #000;
            width: 240px;
            height: 240px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-start;
            font-family: Roboto, serif;
            color: #fff;
            text-align: center
        }

        h1 {
            font-size: 26px;
            margin: 10px 5px;
            font-weight: 700;
            color: orange
        }

        p {
            font-size: 22px;
            margin: 0 5px;
            line-height: 1.25
        }
    </style>
</head>
<body>
<h1>subject</h1>
<p>text</p>
</body>
</html>"""
