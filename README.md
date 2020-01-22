The Flask script **\_\_init\_\_.py** handles the post requests for all SQL queries made from the client side.

The Bash script **sql.sh** makes the actual SQL queries **TO BE IMPLEMENTED USING ORM SQLAlchemy**.

The Python script **formatted_sql.py** accepts the output of **sql.sh** and puts it in JSON format to then be sent to the client.
