# browser.py
import time
import random
import logging
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger("BotLogger")

def get_full_session(token, id_chat_1, id_chat_2, context_size, channel_name, user_id, user_name, channel_id, ai_function):
    """
    Performs a full cycle in one session:
    Login -> Parsing -> Waiting for response from the passed function ai_function -> Printing -> Exit
    """
    driver = None
    try:
        """
        # On Windows, the browser opens with its own arguments.
        options = Options()
        # options.add_argument("--headless") 
        options.add_experimental_option("detach", False)
        driver = webdriver.Chrome(options=options)
        """
        # On Debian, opening a browser with its arguments
        options = Options()
        options.add_argument("--headless=new") # New headless format for Chrome
        options.add_argument("--no-sandbox")   # Mandatory for Linux
        options.add_argument("--disable-dev-shm-usage") # Protection against memory shortage on VDS
        # options.add_experimental_option("detach", False) # In headless, this is not needed
        driver = webdriver.Chrome(options=options)

        # 1. Логин
        driver.get("https://discord.com/login")
        WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")

        driver.execute_script(f"""
            (function() {{
                const authInterval = setInterval(() => {{
                    document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"{token}"`;
                }}, 50);
                setTimeout(() => {{ clearInterval(authInterval); location.href = "https://discord.com/channels/@me"; }}, 2500);
            }})();
        """)

        # 2. Transition to the channel
        target_url = f"https://discord.com/channels/{id_chat_1}/{id_chat_2}"
        logger.info(f"Transition to the channel: {target_url}")
        time.sleep(random.uniform(3, 5)) # Pause for naturalness
        driver.get(target_url)

        # We are waiting for the input field (an indication that we are in the chat).
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]')))
        
        # 3. Context collection
        js_extract = """
        return (function() {
            const results = [];
            const contents = document.querySelectorAll('div[id^="message-content-"]');
            contents.forEach(node => {
                try {
                    const li = node.closest('li[class*="messageListItem"]');
                    let author = "User";
                    if (li) {
                        const nameNode = li.querySelector('[class*="username_"]');
                        if (nameNode) author = nameNode.getAttribute('data-text') || nameNode.innerText.trim();
                        else {
                            let prev = li.previousElementSibling;
                            while (prev) {
                                const prevName = prev.querySelector('[class*="username_"]');
                                if (prevName) { author = prevName.getAttribute('data-text') || prevName.innerText.trim(); break; }
                                prev = prev.previousElementSibling;
                            }
                        }
                    }
                    results.push(author.split('\\n')[0].trim() + ": " + node.innerText.trim());
                } catch (e) {}
            });
            return results;
        })();
        """
        raw_dialog = driver.execute_script(js_extract) or []
        context = "\n".join(raw_dialog[-context_size:])
        
        if not context:
            logger.warning("Context not collected, terminating the session.")
            return False

        # 4. Getting a response from AI (Browser does not close!)
        logger.info("Context is collected. Requesting a response from AI without closing the browser....")
        ai_response = ai_function(context) # We call the function that was passed as an argument.
        
        if not ai_response:
            logger.error("The AI did not provide an answer. We are closing.")
            return False

        # 5. Printing a message (human simulation)
        textbox = driver.find_element(By.CSS_SELECTOR, 'div[role="textbox"]')
        logger.info(f"Имитируем ввод текста...")
        
        # Print character by character!
        for char in ai_response:
            textbox.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15)) # Random delay between letters
            
        time.sleep(random.uniform(1, 2)) # Think before pressing Enter
        
        driver.execute_script("""
            const ke = new KeyboardEvent('keydown', { bubbles: true, cancelable: true, keyCode: 13, key: 'Enter' });
            document.querySelector('div[role="textbox"]').dispatchEvent(ke);
        """)


        # ... (After pressing Enter via JS) ...
        
        logger.info("Enter pressed. Awaiting publication confirmation...")
        time.sleep(4) # We give the message time to appear in the DOM
        
        # Restarting the JS extractor
        check_dialog = driver.execute_script(js_extract) or []
        
        # Checking the last message
        if check_dialog:
            last_msg = check_dialog[-1].lower()
            # Checking whether the last message contains text from the AI
            # (take the first 20 characters for verification so as not to struggle with spaces)
            if ai_response[:20].lower() in last_msg:
                logger.info(">>> CONFIRMED: Message found in chat! <<<")
                # Log write block (minimum code)

                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Limit answer to 20 characters.
                short_answer = ai_response[:20].replace('\n', ' ')
                
                log_line = f"[{now}] | Channel: {channel_name} | UserID: {user_id} | Name: {user_name} | Msg: {short_answer}...\n"
                
                with open(f"{channel_name}.log", "a", encoding="utf-8") as f:
                    f.write(log_line)
                return True
        
        logger.error("!!! CHECK FAILED: Message did not appear in the chat !!!")
        return False


    except Exception as e:
        logger.error(f"Critical failure in the browser session: {e}")
        return False
    finally:
        if driver:
            driver.quit()