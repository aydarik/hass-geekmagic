# Geek Magic Home Assistant Integration

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

This custom component enables integration with the **Geek Magic** smart display device in Home Assistant.

![Home stats](https://raw.githubusercontent.com/aydarik/hass-geekmagic/refs/heads/main/images/home_stats.jpg) ![Pomodoro](https://raw.githubusercontent.com/aydarik/hass-geekmagic/refs/heads/main/images/pomodoro.jpg)

## Features

- **Sensors**: Monitor free space on the device.
- **Controls**: 
  - Change Themes.
  - Adjust Brightness.
  - Select Images.
- **HTML Rendering & Upload**: Send text or raw HTML to the device, which is rendered to an image and uploaded automatically.

## Installation

### HACS (Recommended)

1.  Open **HACS** in Home Assistant.
2.  Go to **Integrations**.
3.  Click the three dots in the top right corner and select **Custom repositories**.
4.  Add the URL of this repository.
5.  Select **Integration** as the category.
6.  Click **Add**.
7.  Find **Geek Magic** in the integration list and install it.
8.  Restart Home Assistant.

### Manual Installation

1.  Copy the `custom_components/geek_magic` directory to your Home Assistant `config/custom_components/` directory.
2.  Restart Home Assistant.
3.  Go to **Settings > Devices & Services > Add Integration**.
4.  Search for **Geek Magic** and select it.
5.  Enter the **IP Address** of your Geek Magic device.

## Configuration

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

### `geek_magic.send_html`

Sends a message or custom HTML to the device. The content is rendered to a 240x240px JPEG and uploaded.

**Parameters:**

| Name | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| `entity_id` | string | The entity ID of the Geek Magic device (e.g. `sensor.geek_magic_free_space`) | Yes |
| `subject` | string | Title/Subject text to display (inserted into template) | No* |
| `text` | string | Body text to display (inserted into template) | No* |
| `html` | string | Raw HTML to render. Overrides `subject` and `text`. | No* |

*\*Either `html` OR (`subject` and `text`) must be provided.*

**Example: Sending a Notification**
```yaml
action: geek_magic.send_html
target:
  entity_id: select.geek_magic_image
data:
  subject: "Alert"
  text: "Washing Machine Finished!"
```

**Example: Sending Custom HTML**
```yaml
action: geek_magic.send_html
target:
  entity_id: select.geek_magic_image
data:
  html: >
    <html>
      <body style="background: red; color: white;">
        <h1>Warning</h1>
      </body>
    </html>
```

## Render API Requirement

This integration requires an external service to convert HTML to an image if you use the `send_html` feature.

**Recommended Renderer:**
You can use the [Text2Image](https://github.com/aydarik/text2image) service.

**Run with Docker:**
```bash
docker run -d -p 8000:8000 docker.io/aydarik/text2image
```

The service should:
- Accept a POST request.
- Body: `{"html": "<your html>"}`.
- Return: `image/jpeg` binary data.
