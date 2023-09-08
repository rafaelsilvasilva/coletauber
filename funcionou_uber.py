from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.service import Service
from selenium import webdriver
from datetime import datetime
import pandas as pd
import schedule
import time
import sys
import re

#Tem que baixar o selenium, pandas, schedule, datetime e openpyxl

locais = []
coletados = []
nome_arquivo = 'uber.xlsx' #Depois de baixar a planilha tem que renomear para uber.xlsx
numero_celular = ''  # Número de celular (para receber o código).
senha = ''  # Senha da conta Uber.


df_excel_uber = pd.read_excel(nome_arquivo)
origens = list(dict.fromkeys(df_excel_uber.iloc[1:,1].tolist()))
destinos = list(dict.fromkeys(df_excel_uber.iloc[1:,2].tolist()))
horarios = list(dict.fromkeys(df_excel_uber.iloc[1:,3].tolist()))
horarioatual = datetime.now().time().strftime("%H:%M:%S")

#No Linux funciona com isso aqui:
options = webdriver.FirefoxOptions()
options.add_argument('--headless')

browser = webdriver.Firefox(options=options)
browser.get('https://m.uber.com/looking')

#Função só pra mostrar o número de celular com uma visualização melhor
def formataNumero(numero_original):
    numero_original = str(numero_original)
    format_string = "({area_code}) {exchange}-{line_number}"

    if len(numero_original) == 11:
        area_code = numero_original[:2]
        exchange = numero_original[2:7]
        line_number = numero_original[7:]
    else:
        area_code = numero_original[:2]
        exchange = numero_original[2:6]
        line_number = numero_original[6:]

    numero_formatado = format_string.format(area_code=area_code, exchange=exchange, line_number=line_number)
    return str(numero_formatado)

#Essas exceções é porque nem sempre ele entra de primeira só com o código
def loginUber():

    def telainicial():
        global codigo        
        browser.find_element("id", "PHONE_NUMBER_or_EMAIL_ADDRESS").send_keys(numero_celular)
        browser.find_element("id", "forward-button").click()

    for origem in range(len(origens)):

        while True:
            try:
                if browser.find_element("id", "PHONE_NUMBER_or_EMAIL_ADDRESS"):
                    telainicial()
                    time.sleep(10)
                    browser.find_element("id", "PASSWORD").send_keys(senha)
                    browser.find_element("id", "forward-button").click()
            except NoSuchElementException:       
                try:
                    while True:
                        try:
                            if browser.find_element("id", "PHONE_SMS_OTP-0"): #Quando entra com o código
                                codigo = input("Digite o código do Uber que chegou no celular "+formataNumero(numero_celular)+" : ")
                                digitos_codigo = [int(digito) for digito in codigo]
                                if codigo.isnumeric():
                                    if len(digitos_codigo) == 4 or len(digitos_codigo) == 6:
                                        break
                                    else:
                                        continue
                                else:
                                    print("Saindo...")
                                    browser.quit()
                                    break
                        except:
                            try:
                                if browser.find_element("xpath", "/html/body/div[5]/div[2]/div/div/div/div/h1"):
                                    print("Muitas tentativas!")
                                    browser.quit()
                                    break
                                    sys.exit(0)
                            except:
                                print("Código não digitado ou não foi possível usar esse número de telefone!")
                                browser.quit()
                                break

                    try: #Quando pede 6 números ao invés de 4
                        browser.find_element("id", "PHONE_SMS_OTP-0").send_keys(digitos_codigo[0])
                        browser.find_element("id", "PHONE_SMS_OTP-1").send_keys(digitos_codigo[1])
                        browser.find_element("id", "PHONE_SMS_OTP-2").send_keys(digitos_codigo[2])
                        browser.find_element("id", "PHONE_SMS_OTP-3").send_keys(digitos_codigo[3])
                    except:
                        pass

                    try:
                        browser.find_element("id", "PHONE_SMS_OTP-4").send_keys(digitos_codigo[4])
                        browser.find_element("id", "PHONE_SMS_OTP-5").send_keys(digitos_codigo[5])
                    except:
                        pass

                    time.sleep(10)

                    try:
                        if browser.find_element("id", "PASSWORD"): #Quando pede senha
                            browser.find_element("id", "PASSWORD").send_keys(senha)
                            browser.find_element("id", "forward-button").click()
                            break
                    except NoSuchElementException:
                        pass

                    try:
                        if browser.find_element("id", "alt-alternate-forms-option-modal"): #Quando abre um menu do nada
                            browser.find_element("id", "alt-alternate-forms-option-modal").click()
                            time.sleep(5)
                            browser.find_element("xpath", "/html/body/div[1]/div[2]/div/div[2]/div/div/div/div/button[3]").click()
                            break
                    except NoSuchElementException:
                        pass

                    try:
                        if browser.find_element("id", "alt-PASSWORD"):
                            browser.find_element("id", "alt-PASSWORD").click()
                            print("Logando direto com a senha...")
                            browser.find_element("id", "alt-PASSWORD").click()
                            break
                    except NoSuchElementException:
                        pass

                    try:
                        if browser.find_element("xpath", "//input[@placeholder='Add a pickup location']"):
                            break
                    except:
                        print("Deu ruim... Tentando novamente...")
                        browser.quit()
                        telainicial()
                            
                except NoSuchElementException:
                    break
                
        while True:
            WebDriverWait(browser, 30).until(
                EC.presence_of_element_located(("xpath", "//input[@placeholder='Add a pickup location']"))
            )
            if browser.find_element("xpath", "//input[@placeholder='Add a pickup location']"):
                break
            continue

        print("Logado no Uber!")
        return True

def fazColeta(origens, destinos):
    global coletados
    for i in range(len(origens)):

        def enviar(caminho):
            caminho = str(caminho).split("-")[0] #Gambiarra (tive que fazer isso pra ele clicar no nome do local no menu do Uber)
            try:
                browser.find_element("xpath", "//p[@contains(text(), '{caminho}')]").click()
            except:
                browser.find_element("xpath", "/html/body/div[1]/div/div/div[1]/div/div[2]/div[2]/div/span/div/div[3]/ul/li[1]/div[1]").click()
                
        origem = browser.find_element("xpath", "//input[@placeholder='Add a pickup location']")
        destino = browser.find_element("xpath", "//input[@placeholder='Enter your destination']")

        origem.send_keys(origens[i])
        time.sleep(10) #Só funcionou comigo quando esperei um tempão (no mínimo 10 segundos - com menos ele começa a coletar uns locais nada a ver)
        enviar(origens[i])
        time.sleep(10)

        destino.send_keys(destinos[i])
        time.sleep(10)
        enviar(destinos[i])
        time.sleep(10)      

        try:
            try:
                if browser.find_element("xpath", "/html/body/div[1]/div/div/div[1]/div/div[2]/div[2]/div/span/div/div[3]/div/ul/li[1]/div[2]/div/div[1]/div/p"):
                    precos = browser.find_element("xpath", "//html/body/div[1]/div/div/div[1]/div/div[2]/div[2]/div/span/div/div[3]/div/ul/li[1]/div[2]/div/div[1]/div/p").text
            except:
                pass
                
            coletados.append(precos)

            origem.clear()
            origem.clear()
            time.sleep(10)
            destino.clear()
            destino.clear()
            time.sleep(10)
            print(coletados)
        except:
            precos = 0
            coletados.append(precos)

    return coletados

#Localiza o horário, rota, e dia na planilha do Uber
def set_locais(df_excel_uber, date, time, dicionario):
    for rota in dicionario.keys():
        df_excel_uber.loc[(df_excel_uber['Horário'] == time) & (df_excel_uber['Origem'].iloc[1:,] == rota), df_excel_uber.iloc[0] == datetime.strptime(date, '%Y-%m-%d')] = 0
        df_excel_uber.loc[(df_excel_uber['Horário'] == time) & (df_excel_uber['Origem'].iloc[1:,] == rota), df_excel_uber.iloc[0] == datetime.strptime(date, '%Y-%m-%d')] = dicionario[rota]

def coleta(horario):
    global locais
    global coletados
    print("Coletando...")
    fazColeta(origens, destinos)
    locais = origens * len(horarios)
    dicionario = dict(zip(locais, coletados))
    hoje = pd.Timestamp.now().strftime('%Y-%m-%d')
    set_locais(df_excel_uber, hoje, horario, dicionario)
    

    with pd.ExcelWriter(nome_arquivo, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df_excel_uber.to_excel(writer, header=False, index=False)

    print("Coleta feitas às: "+str(horarioatual))
    coletados = []

def defineColetas():
    schedule.every().day.at(horarios[0]).do(coleta, horarios[0])
    schedule.every().day.at(horarios[1]).do(coleta, horarios[1])
    schedule.every().day.at(horarios[2]).do(coleta, horarios[2])
    schedule.every().day.at(horarios[3]).do(coleta, horarios[3])

def main():
    loginUber()
    while True:
        defineColetas()
        schedule.run_pending()
        #def formataPlanilha (Ele coleta mais cria uma nova aba ao invés de coletar na planilha do Uber - não sei como manter a formatação)
        #def enviaGoogleDrive (Estava pensando em fazer de uma maneira para que enviasse ao Google Spreadsheets depois de uma coleta)
        time.sleep(60)

if __name__ == "__main__":
    main()
