from re import sub
from pydantic import BaseModel, Field, validator
from typing import Union

{'Город': '', 'Поколение': '', 'Кузов': '', 'Объем двигателя': '', ' л': '', 'Пробег': '', 'Коробка передач': '', 'Привод': '', 'Руль': '', 'Цвет': '', 'Растаможен в Казахстане': '', 'VIN': '', 'Наличие ': ''}

class KolesaData(BaseModel):
    company: str # Компания
    url: str # Ссылка

    brand: str # Марка
    name: str # Модель
    year: int # Год
    price: int # Цена
    description: str # Описание
    
    city: str = Field('', alias='Город') # Город
    generation: str = Field('', alias='Поколение')  # Поколение
    back: str = Field('', alias='Кузов')  # Кузов
    volume: float | str = Field(0, alias='Объем двигателя, л')  # Объем двигателя, л
    volume_type: str = Field('', alias='Объем двигателя, л') # бензин/дизель
    mileage: float | str = Field(0, alias='Пробег') # Пробег
    transmission: str = Field('', alias='Коробка передач') # Привод
    wheel: str = Field('', alias='Руль') # Руль
    wheel_drive: str = Field('', alias='Привод') # Привод
    color: str = Field('', alias='Цвет') # Цвет
    custom_kz: str = Field('', alias='Растаможен в Казахстане') # Растаможен в Казахстане
    vin: str = Field('', alias='VIN') # VIN
    availability: str = Field('', alias='Наличие') # Наличие

    @validator('volume', 'mileage')
    def volume_float(cls, v):
        return float(sub("-?[^\d\.]",'', v)) if v else 0
    
    @validator('volume_type')
    def volume_volume_type(cls, v):
        return v[v.find("(")+1:v.find(")")] if v else ''




