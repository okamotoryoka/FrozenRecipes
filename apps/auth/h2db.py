import jaydebeapi

def get_connection():
    return jaydebeapi.connect(
        "org.h2.Driver",
        "jdbc:h2:file:C:/Users/r_okamoto/recipes",
        ["sa", ""],
        jars="C:\\test1_app\\flaskbook\\flaskbook_racipes\\apps\\recipe\\h2-2.4.240.jar"
    )