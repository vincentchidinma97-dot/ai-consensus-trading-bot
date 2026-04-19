#!/usr/bin/env python3
"""
MetaAPI Forex Trading Bot v2 - Compatible with MetaAPI SDK 29.1.1
"""

import asyncio
import logging
import os
from dotenv import load_dotenv
from metaapi_cloud_sdk import MetaApi

# Load environment variables
load_dotenv(os.path.expanduser('~/.env'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    token = os.getenv('METAAPI_TOKEN')
    account_id = os.getenv('METAAPI_ACCOUNT_ID')
    
    if not token or not account_id:
        logger.error("Missing METAAPI_TOKEN or METAAPI_ACCOUNT_ID in .env file")
        return
    
    logger.info(f"Starting Forex Bot with account: {account_id}")
    
    try:
        api = MetaApi(token)
        account = await api.metatrader_account_api.get_account(account_id)
        
        logger.info(f"✅ Connected to account: {account_id}")
        logger.info(f"Account state: {account.state}")
        logger.info(f"Login: {account.login}")
        logger.info(f"Server: {account.server}")
        
        # Check if account needs deployment
        if account.state == 'UNDEPLOYED':
            logger.info("⏳ Account is UNDEPLOYED. Waiting for manual deployment via MetaAPI dashboard...")
            logger.info("Go to MetaAPI dashboard and click 'Deploy' on your account")
        elif account.state == 'DEPLOYED':
            logger.info("✅ Account is deployed!")
            await asyncio.sleep(2)
            if await account.is_connected():
                logger.info("✅ Connected to MetaTrader!")
                try:
                    account_info = await account.get_account_information()
                    logger.info(f"💰 Balance: ${account_info['balance']}")
                    logger.info(f"💰 Equity: ${account_info['equity']}")
                except:
                    pass
        
        logger.info("\n✅ Bot is ready!")
        logger.info("Press Ctrl+C to stop\n")
        while True:
            await asyncio.sleep(60)
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(main())
