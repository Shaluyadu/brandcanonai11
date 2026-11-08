/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Example: expose the backend URL to the client
  env: {
    BACKEND_URL: process.env.BACKEND_URL || 'http://localhost:8000',
  },
};
module.exports = nextConfig;