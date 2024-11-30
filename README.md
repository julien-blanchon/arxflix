
![ArXFlix](./assets/image/llama6.png)

# ArXFlix

[![Arxflix - Youtube](https://img.shields.io/badge/Arxflix-Youtube-red)](https://www.youtube.com/@Arxflix)
[![Arxflix - X](https://img.shields.io/badge/Arxflix-X-black)](https://x.com/arxflix)

ArXFlix converts research papers into two-minute video summaries, providing all the key information in a visual format.

Example:

[![Your Transformer Might Be Linear!](https://img.youtube.com/vi/FqGK-FDztgg/default.jpg)](https://youtu.be/FqGK-FDztgg)
[![Florence 2: The Future of Unified Vision Tasks!](https://img.youtube.com/vi/umc-jUMqrmE/default.jpg)](https://youtu.be/umc-jUMqrmE)
[![Kandinsky: Revolutionizing Text to Image Synthesis with Prior Models & Latent Diffusion](https://img.youtube.com/vi/1HptxaIGywk/default.jpg)](https://youtu.be/1HptxaIGywk)


## Installation and Usage

### Prerequisites

- **Backend:** Python 3.9+, FFmpeg, pnpm
- **Frontend:** Node.js, pnpm

### Backend

1. **Clone the repository:**

   ```bash
   git clone https://github.com/julien-blanchon/arxflix.git  # Replace with your repository URL
   cd arxflix
   ```

2. **Navigate to the backend folder:**

   ```bash
   cd backend
   ```

3. **Create and activate a virtual environment (recommended):**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # For Linux/macOS
   .venv\Scripts\activate  # For Windows
   ```

4. **Install backend dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

5. **Install FFmpeg and pnpm (if not already installed):**

   ```bash
   brew install ffmpeg pnpm # macOS
   sudo apt-get install ffmpeg pnpm # Debian/Ubuntu - adjust for your distribution
   ```

6. **Run the backend server:**

   ```bash
   fastapi run main.py
   ```

   The backend server should now be running on port 8000.


### Frontend

1. **Navigate to the frontend folder:**

   ```bash
   cd ../frontend
   ```

2. **Install frontend dependencies:**

   ```bash
   pnpm install
   ```

3. **Generate the API client:**

   ```bash
   pnpm generate-client
   ```

4. **Run the frontend development server:**

   ```bash
   pnpm dev
   ```

   The frontend app should now be running on port 3000 or 3001.



## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Make your changes and commit them.
4. Push your branch to your forked repository.
5. Open a pull request against the main branch of the original repository.


## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=julien-blanchon/arxflix&type=Date)](https://star-history.com/#julien-blanchon/arxflix&Date)


