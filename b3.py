from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from time import sleep
from plyer import notification
import constants
import pandas as pd
import gspread

def toast(title, message, timeout=10):
    notification.notify(
        app_name=constants.APP_NAME,
        title=title,
        message=message,
        timeout=timeout,
    )

def element_click_manipulation(wait, driver, element, element_type):
    try:
        element_manipulated = wait.until(EC.element_to_be_clickable((element_type, element)))
        element_manipulated.click()
    except ElementClickInterceptedException:
        print(f"Trying to click on the button {element} again")
        driver.execute_script("arguments[0].click()", element_manipulated)

def select_manipulation(driver, element, element_type, element_value):
    select_element = driver.find_element(element_type, element)
    select_object = Select(select_element)
    select_object.select_by_visible_text(element_value)

    driver.implicitly_wait(8)

def get_url_report(company):

    driver, wait = get_banks_report()[1]

    element_click_manipulation(wait, driver, f'//div[@class="card-body"]//h5[text()="{company}"]', By.XPATH)
    sleep(5)

    try:
        select_report = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'[formcontrolname="selectMenu"]')))
        select_report_object = Select(select_report)
        select_report_object.select_by_visible_text('Relatórios Estruturados')
    except:
        return None

    driver.implicitly_wait(8)
    sleep(5)

    report_url = driver.find_element(By.PARTIAL_LINK_TEXT, 'Demonstrações Financeiras Padronizadas')

    return report_url.get_property('href')

def get_banks_report():

    option = Options()
    option.headless = True
    driver = webdriver.Chrome(options=option)
    wait = WebDriverWait(driver, 20)

    driver.get(constants.COMPANIES_LIST_URL)
    driver.implicitly_wait(8)

    iframe = driver.find_element(by=By.ID, value="bvmf_iframe")
    driver.switch_to.frame(iframe)
    driver.implicitly_wait(8)

    element_click_manipulation(wait, driver, '[href="#accordionClassification"]', By.CSS_SELECTOR)
    
    select_manipulation(driver, '[formcontrolname="selectSector"]', By.CSS_SELECTOR, 'Financeiro')
    
    element_click_manipulation(wait, driver, 'Bancos', By.LINK_TEXT)
    
    select_manipulation(driver, 'selectPage', By.ID, '120')
    sleep(1)
    
    banks = driver.find_elements(By.CLASS_NAME, 'card-body')

    list_banks = []
    for bank in banks:
        bank_short_name = bank.find_element(By.TAG_NAME, 'h5').text
        bank_name = bank.find_element(By.CLASS_NAME, 'card-text').text
        list_banks.append([bank_short_name, bank_name])
    
    return [list_banks, [driver, wait]]

def get_dre_report(bank, report_name):
    
    url = get_url_report(bank)

    if url is None:
        return None
    print(url)

    option = Options()
    option.headless = True
    driver = webdriver.Chrome(options=option)

    driver.get(url)
    driver.implicitly_wait(1)

    select_manipulation(driver, 'cmbQuadro', By.ID, report_name)
    sleep(1)

    iframe = driver.find_element(by=By.TAG_NAME, value="iframe")
    driver.switch_to.frame(iframe)
    driver.implicitly_wait(1)

    table = driver.find_element(By.ID, "ctl00_cphPopUp_tbDados").get_attribute("outerHTML")
    
    # print(table)

    # sleep(20)

    driver.quit()

    return table

def transform_to_dataframe(table, categorical_columns, bank_name):
    if table is not None:
        df = pd.read_html(str(table),encoding = 'utf-8', decimal=',', thousands='.')[0]
        
        columns = df.iloc[0]
        for i, column in enumerate(columns):
            if '/' not in column:
                columns[i] = column
            else:
                columns[i] = column[-4:]

        df = df.iloc[1: , :]
        df.columns = columns

        categorical_columns = categorical_columns
        floats_columns = list(df.iloc[:,2:].columns)

        df[categorical_columns] = df[categorical_columns].astype('category')

        # Remove null values
        df[floats_columns] = df[floats_columns].fillna(value=0)
        df[floats_columns] = df[floats_columns].astype('float64')
        df["Nome do Banco"] = bank_name
        # print(df.head(10))
        # sleep(60)

        return df

def send_to_google_sheets(bank, df, sheet_name):
    name = f'{bank}_{sheet_name}'
    gc = gspread.service_account(filename=constants.SA_GOOGLE_SHEETS)
    sh = gc.open_by_key(constants.DRE_REPORT_SHEET_KEY)

    try:
        worksheet = sh.add_worksheet(name, rows=df.shape[0], cols=df.shape[1])
    except:
        sh.del_worksheet(sh.worksheet(name))
        worksheet = sh.add_worksheet(name, rows=df.shape[0], cols=df.shape[1])
    
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

def store_data(bank, df):
    df.to_csv(f'data/{bank}.csv', sep=',', index=False)

def get_initials(fullname):
    xs = (fullname)
    name_list = xs.split()

    initials = ""

    for name in name_list:
        initials += name[0].upper()
    return initials