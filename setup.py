"""Setup script for Kase Agent."""
from setuptools import setup, find_packages

setup(
    name="kase-agent",
    version="1.0.0",
    description="Kase Agent — The next-generation AI agent by Kyssta",
    author="Kyssta",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "kase=kase.cli.main:main",
            "kase-web=kase.web_panel.server:main",
            "kase-acp=kase.acp.server:run_acp_server",
            "kase-gateway=kase.gateway.run:run_gateway",
        ],
    },
    install_requires=[
        "openai>=1.0.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.27.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "jinja2>=3.1.0",
        "pydantic>=2.0.0",
        "prompt_toolkit>=3.0.40",
        "croniter>=1.4.0",
    ],
    extras_require={
        "anthropic": ["anthropic>=0.30.0"],
        "dev": ["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "ruff>=0.3.0"],
        "messaging": ["python-telegram-bot>=20.0", "aiohttp>=3.9.0"],
    },
)
