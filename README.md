# Geek Magic Home Assistant Integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-blue)](https://hacs.xyz) [![License](https://img.shields.io/github/license/aydarik/hass-geekmagic)](/LICENSE) [![Release](https://img.shields.io/github/v/release/aydarik/hass-geekmagic)](https://github.com/aydarik/hass-geekmagic/releases) [![Downloads](https://img.shields.io/github/downloads/aydarik/hass-geekmagic/latest/geek_magic.zip?displayAssetName=false
)](https://github.com/aydarik/hass-geekmagic/releases) [![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-orange?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/aydarik)

This custom component enables integration with the **Geek Magic** smart display device in Home Assistant.

The latest tested and supported official firmware version
is [Ultra-V9.0.43](https://github.com/GeekMagicClock/smalltv-ultra/tree/main/Ultra-V9.0.43).

> [!TIP]
> Also supports custom firmwares, which are designed with backward compatibility.
>
> 🚀 Currently focused: [aydarik/geekmagic-tv-esp8266](https://github.com/aydarik/geekmagic-tv-esp8266).

## Features

- **Controls**:
    - Change themes.
    - Adjust brightness.
    - Select images.
- **Sensors**: Monitor free space on the device.

- **On custom firmwares**:
    - Send custom messages.
    - Start countdown timers.
    - Attach sticky notes.

![Controls](/images/screenshot_controls.png)

- **HTML Rendering & Upload**: Send text or raw HTML to the device, which is rendered to an image and uploaded
  automatically.

![Home stats](/images/photo_home_stats.jpg) ![Pomodoro](/images/photo_pomodoro.jpg)

- **Image Upload**: Send an image from a local path (e.g., camera snapshot) or URL to the device. The image will be
  automatically resized based on the selected mode.

![Image upload](/images/photo_image.jpg)

## Alternatives

This integration is intended to remain simple, based on the assumption that HTML/CSS/JS already provide sufficient
flexibility to render data in many different ways. With scripting and automation in Home Assistant itself, it’s also
quite easy to build more complex logic when needed (see the [Pomodoro timer](/examples/script.pomodoro.yaml) as an
example).

If you’re looking for a more feature-rich solution, you may want to check out
the [GeekMagic Display for Home Assistant](https://github.com/adrienbrault/geekmagic-hacs) integration
by [@adrienbrault](https://github.com/adrienbrault).

## Installation

### HACS (Recommended)

[![Add to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=aydarik&repository=hass-geekmagic&category=integration)

or manually:

1. Open **HACS** in Home Assistant.
2. Find **Geek Magic** in the integration list and install it.
3. Restart Home Assistant.

### Manual Installation

1. Download and unpack the latest [release](https://github.com/aydarik/hass-geekmagic/releases) zip file to your Home
   Assistant `config/custom_components/geek_magic` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings > Devices & Services > Add Integration**.
2. Search for **Geek Magic**.

### Basic Setup

During the initial setup, you need to provide the device's IP address. You can also optionally configure the **Render
URL** and **HTML Template** at this stage.

### Advanced Options (HTML Rendering)

If you skipped configuring the Render URL during setup, you can do it later:

1. Go to **Settings > Devices & Services**.
2. Click **Geek Magic**.
3. Click **Configure**.
4. **Render URL**: Enter the URL of your rendering service (e.g., `http://127.0.0.1:8000/render`).
5. **HTML Template**: (Optional) Customize the default HTML template used when sending simple subject/text messages.

## Services

### Send HTML

Sends a message or custom HTML to the device. The content is rendered to a 240x240px JPEG and uploaded.

#### Parameters

| Name        | Type    | Description                                                                                     | Required             |
|:------------|:--------|:------------------------------------------------------------------------------------------------|:---------------------|
| `device_id` | string  | The device IDs of the Geek Magic devices to send to (broadcast to all devices if not specified) | No                   |
| `subject`   | string  | Title/Subject text to display (inserted into template)                                          | No*                  |
| `text`      | string  | Body text to display (inserted into template)                                                   | No*                  |
| `html`      | string  | Raw HTML to render. Overrides `subject` and `text`.                                             | No*                  |
| `cache`     | boolean | Whether to use cached results for the render service.                                           | No (default: `true`) |

*\*Either `html` OR (`subject` and `text`) must be provided.*

#### Examples

<details>
<summary>Simple Notification</summary>

```yaml
action: geek_magic.send_html
data:
  subject: "Alert"
  text: "🌡️ The current temperature is too high: {{ states('sensor.your_temperature_sensor') | round(1) }}°C"
```

</details>

![Simple Notification](/images/render_simple.jpg)

<details>
<summary>Formatted Notification</summary>

```yaml
action: geek_magic.send_html
data:
  subject: >-
    ⏳ {{ ((as_timestamp(state_attr('calendar.your_calendar_name', 'start_time')) - as_timestamp(now())) / 60) | round }} minutes
  text: >-
    <p style="padding-top:15px; font-size:28px">🕒 {{ as_timestamp(state_attr('calendar.your_calendar_name', 'start_time')) | timestamp_custom('%H:%M') }} - {{ as_timestamp(state_attr('calendar.your_calendar_name', 'end_time')) | timestamp_custom('%H:%M') }}<p>
    <p style="padding-top:15px; font-size:32px; text-align:center">{{ state_attr('calendar.your_calendar_name', 'message') }}<p>
```

</details>

![Formatted Notification](/images/render_calendar.jpg)

<details>
<summary>Climate</summary>

```yaml
action: geek_magic.send_html
data:
  html: |
    <html>
    <head>
    <style>
      body {
        margin: 0;
        font-family: Roboto, serif;
      }

      .widget {
        width: 240px;
        height: 240px;
        background: #000000;
        color: #e6e6e6;
        overflow: hidden;
      }

      .row {
        display: flex;
        justify-content: space-evenly;
        align-items: stretch;
        font-size: 112px;
      }
    </style>
    </head>
    <body>
    <div class="widget">
      <div class="row">
        <span style="font-size: 40px; padding-right: 2px">🌡️</span>{{ states('sensor.your_temperature_sensor') | round }}<span style="font-size: 48px;">°C</span>
      </div>
      <div class="row">
        <span style="font-size: 40px; padding-right: 2px;">💧</span>{{ states('sensor.your_humidity_sensor') | round }}<span style="font-size: 48px;">%</span>
      </div>
    </div>
    </body>
    </html>
```

</details>

![Climate](/images/render_climate.jpg)

<details>
<summary>Bus Departure</summary>

```yaml
action: geek_magic.send_html
data:
  html: |
    <html>
    <head>
    <style>
      body {
        margin: 0;
        font-family: Roboto, serif;
      }

      .card {
        width: 240px;
        height: 240px;
        background: #000000;
        color: #e6e6e6;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
      }

      .minutes {
        font-size: 168px;
        margin: -20px;
      }

      .label {
        color: #feba01;
      }

      .on-time {
        color: #4ade80;
      }

      .late {
        color: #ff391f;
      }

      .early {
        color: #60a5fa;
      }
    </style>
    </head>
    <body>
    <div class="card">
      <div class="label" style="font-size: 32px;"><img src="https://abfahrtsmonitor.vbb.de/images/transport/bus_blank.svg" width="24" height="24" alt="Bus Logo"> {{ state_attr('sensor.your_bus_sensor', 'name') }}</div>
      <div id="main" class="minutes">-</div>
      <div id="status" style="font-size: 40px;"/>
    </div>

    <script>
      const minsToActual = {{ states('sensor.your_bus_departure_sensor') }};
      const diffSchedActual = {{ '\'unavailable\'' if states('sensor.your_bus_delay_sensor') == 'unavailable' else states('sensor.your_bus_delay_sensor') }};

      const mainEl = document.getElementById("main");
      const statusEl = document.getElementById("status");
      mainEl.textContent = minsToActual;

      if (diffSchedActual == 0) {
        statusEl.textContent = 'on-time';
        statusEl.classList.add("on-time");
      } else if (diffSchedActual > 0) {
        statusEl.textContent = `+${diffSchedActual} min`;
        statusEl.classList.add("late");
      } else if (diffSchedActual < 0) {
        statusEl.textContent = `${diffSchedActual} min`;
        statusEl.classList.add("early");
      } else {
        statusEl.textContent = 'scheduled';
      }

      if (minsToActual <= 2) {
        mainEl.classList.add("late");
      } else if (minsToActual <= 5) {
        mainEl.classList.add("label");
      }
    </script>
    </body>
    </html>
```

</details>

![Bus Departure](/images/render_bus.jpg)

<details>
<summary>BTC Price</summary>

```yaml
action: geek_magic.send_html
data:
  cache: false
  html: |
    <html>
    <head>
    <style>
      html, body {
        margin: 0;
        width: 240px;
        height: 240px;
        overflow: hidden;
        background: #000000;
        color: #e6e6e6;
        font-family: Roboto, serif;
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
        margin-bottom: 15px;
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

### Send image

Sends a JPEG image from a local path or URL to the device. The image will be automatically resized based on the selected
mode.

#### Parameters

| Field         | Type   | Description                                                                                     | Required                |
|---------------|--------|-------------------------------------------------------------------------------------------------|-------------------------|
| `device_id`   | string | The device IDs of the Geek Magic devices to send to (broadcast to all devices if not specified) | No                      |
| `image_path`  | string | Local path (e.g., `/config/www/test.jpg`) or URL (e.g., `https://...`)                          | Yes                     |
| `resize_mode` | string | `stretch` (force 240x240), `fit` (longest side 240) or `crop` (center crop to 240x240)          | No (default: `stretch`) |

#### Examples

<details>
<summary>Sending a local image</summary>

```yaml
action: geek_magic.send_image
data:
  image_path: /config/www/camera/snapshot.jpg
```

</details>

![Local Image](/images/render_image.jpg)

<details>
<summary>Sending an image from a URL</summary>

```yaml
action: geek_magic.send_image
data:
  image_path: >-
    https://www.berlin.de/webcams/rathaus/webcam.jpg
  resize_mode: crop
```

</details>

![URL Image](/images/render_webcam.jpg)

### Send custom message

Sends a custom message to the device. Supported **ONLY on custom firmware**.

#### Parameters

| Field             | Type   | Description                                                                                     | Required |
|-------------------|--------|-------------------------------------------------------------------------------------------------|----------|
| `device_id`       | string | The device IDs of the Geek Magic devices to send to (broadcast to all devices if not specified) | No       |
| `message_style`   | string | Style of the message. Currently supported: `default`, `center`, `big_num`                       | No       |
| `message_subject` | string | Message subject, shown as a title.                                                              | No       |
| `custom_message`  | string | Custom message to show on the Geek Magic device.                                                | Yes      |

#### Examples

<details>
<summary>Sending a custom message</summary>

```yaml
action: geek_magic.send_message
data:
  message_style: center
  message_subject: Notification
  custom_message: |
    Hello world!
    Привет, мир!
  timeout: 60
```

</details>

![Custom message](/images/photo_custom_message.jpg)

<details>
<summary>Sending a value with gauge</summary>

```yaml
action: geek_magic.send_message
data:
  message_style: big_num
  message_subject: Living room
  custom_message: "{{ states('sensor.esp_1_temperature') ~ '/30 ℃' }}"
  timeout: 60
```

</details>

![Gauge](/images/photo_custom_gauge.jpg)

### Start countdown timer

Start a countdown timer to a specified date and time. Supported **ONLY on custom firmware**.

#### Parameters

| Field                | Type   | Description                                                                                     | Required |
|----------------------|--------|-------------------------------------------------------------------------------------------------|----------|
| `device_id`          | string | The device IDs of the Geek Magic devices to send to (broadcast to all devices if not specified) | No       |
| `countdown_subject`  | string | Countdown subject, shown as a title.                                                            | No       |
| `countdown_datetime` | string | Date and time in the format `YYYY-MM-DD HH:mm:ss` or ISO 8601.                                  | Yes      |

#### Examples

<details>
<summary>Starting a countdown timer</summary>

```yaml
action: geek_magic.set_countdown
data:
  countdown_subject: "{{ state_attr('calendar.your_calendar_sensor', 'message') }}"
  countdown_datetime: "{{ state_attr('calendar.your_calendar_sensor', 'start_time') }}"
  timeout: 60
```

</details>

![Countdown](/images/photo_custom_countdown.jpg)

### Set sticky note

Sets a sticky note on the Clock screen. Supported **ONLY on custom firmware**.

#### Parameters

| Field       | Type    | Description                                                                                                                                                                                                           | Required             |
|-------------|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------|
| `device_id` | string  | The device IDs of the Geek Magic devices to send to (broadcast to all devices if not specified)                                                                                                                       | No                   |
| `note`      | string  | Note to show on the Clock screen.                                                                                                                                                                                     | Yes                  |
| `rpm`       | integer | Number of rotations per minute. Cannot be less than the number of lines.<br/>Ideally, 60 divided by this number should result in a whole number.<br/>_Example:_ 4 - every 15 seconds; 60 (max) - every single second. | No                   |
| `force`     | boolean | Whether to force redraw the screen. Otherwise, updates with the next rotation.                                                                                                                                        | No (default: `true`) |

#### Examples

<details>
<summary>Setting sticky note (rotates within a minute)</summary>

```yaml
action: geek_magic.set_note
data:
  note: >-
    {% set weather_state = states('weather.home') | replace('-night', '') |
    replace('-', ' ') | replace('partlycloudy', 'partly cloudy') %}
    {% set weather_temp = state_attr('weather.home', 'temperature') | float |
    round(0) %}

    {% set home_temp = states('sensor.temperature') | round(1) %}
    {% set home_humid = states('sensor.humidity') | round(0) %}

    {{ ('+' if (weather_temp > 0)) ~ weather_temp ~ '℃, ' ~ weather_state }}
    {{ home_temp ~ '℃ | ' ~ home_humid ~ '%' }}
    {{ 'CO₂ ' ~ states('sensor.carbon_dioxide') | round ~ ' ppm' }}
  timeout: 3600 # auto-expires if not updated
```

</details>

![Sticky Note](/images/photo_custom_note.jpg)

## Render API Requirement

This integration requires an external service to convert HTML to an image if you use the `send_html` feature.

### Predefined Renderer

The integration comes with a **predefined renderer** (`https://text2image.gumerbaev.ru/render`) that works out of the
box. However, for privacy reasons, we **strongly recommend** spinning up your own instance, as the HTML content (which
may include sensitive data from your smart home) will be sent to an external server.

### Self-Hosted Renderer (Recommended)

You can use the [Text2Image](https://github.com/aydarik/text2image) service.

#### Home Assistant Add-on

[![Add to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Faydarik%2Fhass-addons)

##### Manual installation

1. Add the repository URL to your Home Assistant Add-on Store repositories:
   `https://github.com/aydarik/hass-addons`
2. Install the "Text2Image" add-on.
3. Start the add-on.

#### Docker

```bash
docker run -d -p 8000:8000 ghcr.io/aydarik/text2image:latest
```

> Then configure the **Render URL** in the integration settings to point to your local instance (e.g.,
`http://127.0.0.1:8000/render`).

### API Specification

If you prefer, you can also implement your own service. It should follow these requirements:

- Accept a POST request.
- Body: `{"html": "<your html>", "cache": true}`.
- Return a 240x240px `image/jpeg` image.

## License

This project is licensed under the MIT License - see the [LICENSE](/LICENSE) file for details.
