# Geek Magic Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue)](https://hacs.xyz) [![License](https://img.shields.io/github/license/aydarik/hass-geekmagic)](/LICENSE) [![Release](https://img.shields.io/github/v/release/aydarik/hass-geekmagic)](https://github.com/aydarik/hass-geekmagic/releases) [![Downloads](https://img.shields.io/github/downloads/aydarik/hass-geekmagic/latest/geek_magic.zip?displayAssetName=false
)](https://github.com/aydarik/hass-geekmagic/releases) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-orange?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/aydarik)

This custom component enables integration with the **Geek Magic** smart display device in Home Assistant.

## Features

- **Controls**: 
  - Change Themes.
  - Adjust Brightness.
  - Select Images.
- **Sensors**: Monitor free space on the device.

![Controls](/images/screenshot_controls.png)

- **HTML Rendering & Upload**: Send text or raw HTML to the device, which is rendered to an image and uploaded automatically.

![Home stats](/images/photo_home_stats.jpg) ![Pomodoro](/images/photo_pomodoro.jpg)

- **Image Upload**: Send an image from a local path (e.g., camera snapshot) or URL to the device. The image will be automatically resized based on the selected mode.

![Image upload](/images/photo_image.jpg)

## Alternatives

This integration is intended to remain simple, based on the assumption that HTML/CSS/JS already provide sufficient flexibility to render data in many different ways. With scripting and automation in Home Assistant itself, it’s also quite easy to build more complex logic when needed (see the [Pomodoro timer](/examples/script.pomodoro.yaml) as an example).

If you’re looking for a more feature-rich solution, you may want to check out the [GeekMagic Display for Home Assistant](https://github.com/adrienbrault/geekmagic-hacs) integration by [@adrienbrault](https://github.com/adrienbrault).

## Installation

### HACS (Recommended)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aydarik&repository=hass-geekmagic&category=integration)

or manually:

1.  Open **HACS** in Home Assistant.
2.  Go to **Integrations**.
3.  Click the three dots in the top right corner and select **Custom repositories**.
4.  Add the URL of this repository.
5.  Select **Integration** as the category.
6.  Click **Add**.
7.  Find **Geek Magic** in the integration list and install it.
8.  Restart Home Assistant.

### Manual Installation

1.  Download and unpack the latest [release](https://github.com/aydarik/hass-geekmagic/releases) zip file to your Home Assistant `config/custom_components/geek_magic` directory.
2.  Restart Home Assistant.

## Configuration

1.  Go to **Settings > Devices & Services > Add Integration**.
2.  Search for **Geek Magic**.

### Basic Setup
During the initial setup, you need to provide the device's IP address. You can also optionally configure the **Render URL** and **HTML Template** at this stage.

### Advanced Options (HTML Rendering)
If you skipped configuring the Render URL during setup, you can do it later:
1.  Go to **Settings > Devices & Services**.
2.  Click **Geek Magic**.
3.  Click **Configure**.
4.  **Render URL**: Enter the URL of your rendering service (e.g., `http://192.168.1.50:8000/render`).
5.  **HTML Template**: (Optional) Customize the default HTML template used when sending simple subject/text messages.

## Services

### Send HTML

Sends a message or custom HTML to the device. The content is rendered to a 240x240px JPEG and uploaded.

#### Parameters

| Name | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `entity_id` | string | The entity ID of the Geek Magic device (e.g. `sensor.geek_magic_image`) | Yes |
| `subject` | string | Title/Subject text to display (inserted into template) | No* |
| `text` | string | Body text to display (inserted into template) | No* |
| `html` | string | Raw HTML to render. Overrides `subject` and `text`. | No* |
| `cache` | boolean | Whether to use cached results for the render service. | No (default: `true`) |

*\*Either `html` OR (`subject` and `text`) must be provided.*

#### Examples

<details>
<summary>Simple Notification</summary>

```yaml
action: geek_magic.send_html
data:
  entity_id: select.geek_magic_image
  subject: "Alert"
  text: "Washing Machine finished!"
```

</details>

![Simple Notification](/images/render_simple.jpg)

<details>
<summary>Formatted Notification</summary>

```yaml
action: geek_magic.send_html
data:
  entity_id: select.geek_magic_image
  subject: Main door
  text: |
    <p style="font-size: 84px; padding: 30px 0">🚪🚶</p>
```

</details>

![Formatted Notification](/images/render_door.jpg)

<details>
<summary>Neon Clock</summary>

```yaml
action: geek_magic.send_html
data:
  entity_id: select.geek_magic_image
  html: |
    <html lang="en">
    <head>
        <title>Neon Clock</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: #121212;
            }

            .clock {
                width: 240px;
                height: 240px;
                border-radius: 50%;
                background: #1e1e1e;
                display: flex;
                justify-content: center;
                align-items: center;
                font-family: Arial, sans-serif;
                font-size: 48px;
                font-weight: bold;
                color: #00ffae;
                box-shadow: 0 0 15px rgba(0, 255, 174, 0.5);
            }
        </style>
    </head>
    <body>
    <div class="clock">{{ as_timestamp(now()) | timestamp_custom('%H:%M') }}</div>
    </body>
    </html>
```

</details>

![Neon Clock](/images/render_clock.jpg)

<details>
<summary>BTC Price</summary>

```yaml
action: geek_magic.send_html
data:
  entity_id: select.geek_magic_image
  html: >
    <html lang="en">
    <head>
    <title>BTC Price</title>
    <meta name="viewport" content="width=240, height=240, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <style>
      * {
        box-sizing: border-box;
      }
    
      html, body {
        margin: 0;
        width: 240px;
        height: 240px;
        overflow: hidden;
        background: #0f1115;
        color: #ffffff;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }
    
      body {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }
    
      #header {
        display: flex;
        align-items: center;
        gap: 8px;
        height: 32px;
        margin-bottom: 4px;
      }
    
      #logo {
        width: 24px;
        height: 24px;
        display: block;
      }
    
      #price {
        font-size: 32px;
        font-weight: 600;
        line-height: 1;
        white-space: nowrap;
      }
    
      canvas {
        width: 220px;
        height: 180px;
        display: block;
      }
    </style>
    </head>
    <body>
    <div id="header">
      <img
        id="logo"
        src="https://assets.coingecko.com/coins/images/1/standard/bitcoin.png"
        alt="Bitcoin"
        loading="eager"
        decoding="sync"
      />
      <div id="price">Loading…</div>
    </div>
    <canvas id="chart" width="220" height="180"></canvas>
    <script>
    // TIMESTAMP for cache update:
    // {{ (as_timestamp(now()) / 60) | round }}
    
    const PRICE_URL =
      "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd";
    
    const CHART_URL =
      "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1";
    
    async function loadData() {
      try {
        const [priceRes, chartRes] = await Promise.all([
          fetch(PRICE_URL),
          fetch(CHART_URL)
        ]);
    
        if (!priceRes.ok || !chartRes.ok) throw new Error("API error");
    
        const priceData = await priceRes.json();
        const chartData = await chartRes.json();
    
        const prices = chartData.prices.map(p => p[1]);
        const current = priceData.bitcoin.usd;
    
        document.getElementById("price").textContent =
          `$${current.toLocaleString("en-US")}`;
    
        const trendUp = prices[prices.length - 1] >= prices[0];
        drawChart(prices, trendUp);
    
      } catch (e) {
        document.getElementById("price").textContent = e.message;
        drawChart([], true);
      }
    
      window.renderReady = true;
    }
    
    function drawChart(values, trendUp) {
      const canvas = document.getElementById("chart");
      const ctx = canvas.getContext("2d", { alpha: true });
    
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    
      if (values.length < 2) return;
    
      const min = Math.min(...values);
      const max = Math.max(...values);
      const range = max - min || 1;
    
      ctx.strokeStyle = trendUp ? "#22c55e" : "#ef4444";
      ctx.lineWidth = 2;
      ctx.lineJoin = "round";
      ctx.lineCap = "round";
    
      ctx.beginPath();
    
      values.forEach((v, i) => {
        const x = (i / (values.length - 1)) * canvas.width;
        const y = canvas.height - ((v - min) / range) * canvas.height;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
    
      ctx.stroke();
    }
    
    loadData()
    </script>
    </body>
    </html>
```

</details>

![BTC Price](/images/render_btc.jpg)

### Send Image

Sends a JPEG image from a local path or URL to the device. The image will be automatically resized based on the selected mode.

#### Parameters

| Field | Type | Description | Required |
| --- | --- | --- | --- |
| `entity_id` | string | The entity ID of the Geek Magic device (e.g. `sensor.geek_magic_image`) | Yes |
| `image_path` | string | Local path (e.g., `/config/www/test.jpg`) or URL (e.g., `https://...`) | Yes |
| `resize_mode` | string | `stretch` (force 240x240), `fit` (longest side 240) or `crop` (center crop to 240x240) | No (default: `stretch`) |

#### Examples

<details>
<summary>Sending a local image</summary>

```yaml
action: geek_magic.send_image
data:
  entity_id: select.geek_magic_image
  image_path: /config/www/tmp/snapshot_tapo_c200_c094.jpg
```

</details>

![Local Image](/images/render_image.jpg)

<details>
<summary>Sending an image from a URL</summary>

```yaml
action: geek_magic.send_image
data:
  entity_id: select.geek_magic_image
  image_path: >-
    https://www.berlin.de/webcams/rathaus/webcam.jpg
  resize_mode: crop
```

</details>

![URL Image](/images/render_webcam.jpg)

## Render API Requirement

This integration requires an external service to convert HTML to an image if you use the `send_html` feature.

### Predefined Renderer

The integration comes with a **predefined renderer** (`https://text2image.gumerbaev.ru/render`) that works out of the box. However, for privacy reasons, we **strongly recommend** spinning up your own instance, as the HTML content (which may include sensitive data from your smart home) will be sent to an external server.

### Self-Hosted Renderer (Recommended)

You can use the [Text2Image](https://github.com/aydarik/text2image) service.

#### Home Assistant Add-on

[![Add to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Faydarik%2Fhass-addons)

##### Manual installation

1.  Add the repository URL to your Home Assistant Add-on Store repositories:
    `https://github.com/aydarik/hass-addons`
2.  Install the "Text2Image" add-on.
3.  Start the add-on.

#### Docker

```bash
docker run -d -p 8000:8000 ghcr.io/aydarik/text2image:latest
```

> Then configure the **Render URL** in the integration settings to point to your local instance (e.g., `http://127.0.0.1:8000/render`).

### API Specification

If you prefer, you can also implement your own service. It should follow these requirements:
- Accept a POST request.
- Body: `{"html": "<your html>", "cache": true}`.
- Return a 240x240px `image/jpeg` image.

## License

This project is licensed under the MIT License - see the [LICENSE](/LICENSE) file for details.
