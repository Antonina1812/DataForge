import json
from jsonschema import validate, ValidationError

def validate_json_schema(data, schema):
    """
    Проверяет JSON данные на соответствие схеме.

    Args:
        data: JSON данные (Python объект).
        schema: JSON схема (Python объект).

    Returns:
        True, если данные соответствуют схеме, False в противном случае.
    """
    try:
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        print(f"JSON Schema validation error: {e}") # Логируем ошибку для отладки
        return False

def autodetect_json_schema(data):
  """
  Автоматически определяет схему JSON на основе предоставленных данных.
  
  Args:
    data: JSON данные (Python объект)

  Returns:
     JSON схема (Python объект)
  """
  if isinstance(data, list):
    # Если корневой элемент - список, предполагаем, что все элементы имеют одинаковую структуру
    if data:
      return autodetect_json_schema(data[0])  # Рекурсивно вызываем для первого элемента
    else:
      return {"type": "array"}  # Пустой список
  elif isinstance(data, dict):
    schema = {"type": "object", "properties": {}}
    for key, value in data.items():
      if isinstance(value, str):
        schema["properties"][key] = {"type": "string"}
      elif isinstance(value, int):
        schema["properties"][key] = {"type": "integer"}
      elif isinstance(value, float):
        schema["properties"][key] = {"type": "number"}
      elif isinstance(value, bool):
        schema["properties"][key] = {"type": "boolean"}
      elif isinstance(value, list):
        #Обработка массивов.  Предполагаем, что все элементы массива одного типа
        if value:
          element_schema = autodetect_json_schema(value[0])  #Рекурсия для первого элемента массива
          schema["properties"][key] = {"type": "array", "items": element_schema}
        else:
          schema["properties"][key] = {"type": "array"} #Пустой массив
      elif value is None:
          schema["properties"][key] = {"type": "null"} # Значение None
      else:
        schema["properties"][key] = autodetect_json_schema(value)  # Рекурсия для вложенных объектов
    schema["required"] = list(data.keys())  # Все ключи считаются обязательными
    return schema
  else:
    return {"type": type(data).__name__}  # Простые типы данных