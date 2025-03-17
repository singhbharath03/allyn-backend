# Allyn Backend

## Setup Instructions

1. Clone the repository:
   ```
   git clone https://github.com/singhbharath03/allyn-backend
   cd allyn-backend
   ```

2. Create a `.env.local` file with the required environment variables:
   ```
   PRIVATE_KEY=your_private_key_here
   ```

3. Build and start the Docker containers:
   ```
   docker compose up -d
   ```

4. Run all Django migrations:
   ```
   ./backend/docker_manage.py migrate
   ```

5. Check logs:
   ```
   sudo docker compose logs -f --tail 100
   ``` 