import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from time import sleep

service = Service(executable_path="/path/to/chromedriver")
driver = webdriver.Chrome(service=service)


class scorePrestador:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome(service=service,
                                       executable_path="/caminho/para/chromedriver")

    def login(self):
        driver = self.driver
        driver.get("https://prestador.example.invalid/login")
        sleep(8)
        inputUser = driver.find_element("xpath", "//input[@name='username']")
        inputUser.click()
        inputUser.clear()
        inputUser.send_keys(self.username)
        sleep(0.5)
        inputPassword = driver.find_element(
            "xpath", "//input[@name='password']")
        inputPassword.click()
        inputPassword.clear()
        inputPassword.send_keys(self.password)
        sleep(1)
        inputPassword.send_keys(Keys.ENTER)
        sleep(10)

    def records(self):
        driver = self.driver
        record = driver.find_element(
            By.XPATH, "//*[@id='🚐']/div[1]/div/div[1]/ul/div[2]/li[2]/a")
        record.click()
        sleep(2)

    def search(self):
        driver = self.driver
        input_pesq = driver.find_element(
            By.XPATH, "//*[@id='🚐']/div[1]/div/div[2]/div[1]/form/div/input")
        arq_df = pd.read_csv("pedidos.csv")
        request = list(arq_df["Pedido"])
        print(f'-----> Foram encontrados {len(request)} pedidos nessa lista.')
        print(f'-----> Esses foram os pedidos {request}')
        for c in range(len(request)):
            input_pesq.click()
            input_pesq.clear()
            input_pesq.send_keys(request[c])
            sleep(2)
            try:
                search_result = driver.find_element(
                    "xpath", "//span[@title='Concluído']")
                search_result.click()
                sleep(4)
                score = driver.find_element(
                    By.XPATH, "//span[@class='style__Text-sc-1ubn63g-8 fGthnO']").text.replace(".", ",")
                arq_df.loc[c, "Score"] = score
                arq_df.loc[c, "Status"] = "verificado"
                arq_df.to_csv("pedidos.csv")
                exit_result = driver.find_element(
                    "xpath", "//button[@class='style__Base-sc-vh04nt-0 Button__StyledButton-sc-1gmuxjw-3 iETTwv bKXePp']")
                sleep(1)
                exit_result.click()
                input_pesq.send_keys(Keys.CONTROL, 'a')
                input_pesq.send_keys(Keys.BACKSPACE)
            except:
                try:
                    not_result = driver.find_element(
                        "xpath", "//span[@title='Cancelado']")
                    if not_result:
                        arq_df.loc[c, "Score"] = "N/E"
                        arq_df.loc[c, "Status"] = "Cancelado"
                        arq_df.to_csv("pedidos.csv")
                    sleep(2)
                except:
                    arq_df.loc[c, "Score"] = "N/E"
                    arq_df.loc[c, "Status"] = "Pedido não encontrado"
                    arq_df.to_csv("pedidos.csv")
                finally:
                    input_pesq.send_keys(Keys.CONTROL, 'a')
                    input_pesq.send_keys(Keys.BACKSPACE)
                    sleep(2)

    def quit(self):
        driver = self.driver
        driver.quit()


rochaBot = scorePrestador('username', 'password')
rochaBot.login()
rochaBot.records()
rochaBot.search()
rochaBot.quit()
