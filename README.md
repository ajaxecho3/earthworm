# Earthworm web-crawler

This is a simple web-crawler application that fetches and processes web pages. It is designed to be run as a Python package.
It includes a main module that can be executed directly, and it is structured to allow for easy expansion and integration with other components.

## Setup and Run

This project uses the [uv](https://github.com/astral-sh/uv) package manager for fast Python environment management.
To run the application, follow these steps:

1. **Install uv**: If you haven't already, install the `uv` package manager.

   ```bash
   pip install uv
   ```

2. **Run the application**: Navigate to the `app` directory and run the main module.

   ```bash
   cd app
   uv run main.py
   ```  

3. **Direct execution**: You can also run the application directly from the root directory.

   ```bash
   uv run -m app.main
    ```
