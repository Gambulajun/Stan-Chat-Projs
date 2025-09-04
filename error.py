ValueError
ValueError: not enough values to unpack (expected 4, got 3)

Traceback (most recent call last)
File "C:\Users\2030644\AppData\Roaming\Python\Python313\site-packages\flask\app.py", line 1536, in __call__
return self.wsgi_app(environ, start_response)
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\2030644\AppData\Roaming\Python\Python313\site-packages\flask\app.py", line 1514, in wsgi_app
response = self.handle_exception(e)
           ^^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\2030644\AppData\Roaming\Python\Python313\site-packages\flask\app.py", line 1511, in wsgi_app
response = self.full_dispatch_request()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\2030644\AppData\Roaming\Python\Python313\site-packages\flask\app.py", line 919, in full_dispatch_request
rv = self.handle_user_exception(e)
     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\2030644\AppData\Roaming\Python\Python313\site-packages\flask\app.py", line 917, in full_dispatch_request
rv = self.dispatch_request()
     ^^^^^^^^^^^^^^^^^^^^^^^
File "C:\Users\2030644\AppData\Roaming\Python\Python313\site-packages\flask\app.py", line 902, in dispatch_request
return self.ensure_sync(self.view_functions[rule.endpoint])(**view_args)  # type: ignore[no-any-return]
       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "c:\Users\2030644\Main_Project1\app.py", line 117, in decorated_function
return f(*args, **kwargs)
       ^^^^^^^^^^^^^^^^^^
File "c:\Users\2030644\Main_Project1\app.py", line 243, in view_resources
ok, clash_audit, _, _ = is_range_available(emp_id_int,
^^^^^^^^^^^^^^^^^^^^^
ValueError: not enough values to unpack (expected 4, got 3)
The debugger caught an exception in your WSGI application. You can now look at the traceback which led to the error.
To switch between the interactive traceback and the plaintext one, you can click on the "Traceback" headline. From the text traceback you can also create a paste of it. For code execution mouse-over the frame you want to debug and click on the console icon on the right side.

You can execute arbitrary Python code in the stack frames and there are some extra helpers available for introspection:

dump() shows all variables in the frame
dump(obj) dumps all that's known about the object
