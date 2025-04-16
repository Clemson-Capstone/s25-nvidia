/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    env: {
        NEXT_PUBLIC_ENABLE_GUARDRAILS_TOGGLE: process.env.ENABLE_GUARDRAILS_TOGGLE || 'false',
    },
};

export default nextConfig;
