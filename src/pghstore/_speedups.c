#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdio.h>
#include <string.h>

struct module_state {
    PyObject *error;
};

#ifndef IS_PY3
#define IS_PY3 PY_MAJOR_VERSION == 3
#endif

#ifndef IS_PY2
#define IS_PY2 PY_MAJOR_VERSION == 2
#endif

#if IS_PY3
#define GETSTATE(m) ((struct module_state*)PyModule_GetState(m))
#endif

#define DEBUG_PRINT 0
#define debug_print(fmt, ...) do { if (DEBUG_PRINT) fprintf(stderr, fmt, __VA_ARGS__); } while (0)


#define isEven(a) (((a) & 1) == 0)

#define ConcatOrGotoCleanup(result, string) { PyBytes_Concat(&result, string); if (!result) { goto _speedup_dumps_cleanup_and_exit; } }

/*
 * Just like strchr, but find first -unescaped- occurrence of c in s.
 */
char *
strchr_unescaped(char *s, Py_ssize_t length, char c) 
{
  char *end = s + length;
  debug_print( "looking for p: s[%c, %p]\n", *s,  s);
  char *p = memchr(s, c, length), *q;
  debug_print( "found p: [%c, %p]\n", *p,  p);
  while (p != NULL) { /* loop through all the c's */
    q = p; /* scan backwards through preceding escapes */
    while (q > s && *(q-1) == '\\') {
      q--;
    }
    if (isEven(p-q)){ /* even number of esc's => c is good */
        debug_print( "found p: s[%c, %p]\n", *p,  p);
        return p;
    }
    p = memchr(p+1, c, end - (p + 1)); /* else odd escapes => c is escaped, keep going */
  }
  return NULL;
}

/* Written to match pghstore._native.unescape but slightly smarter. */
PyObject *
unescape(char *copy_from_start, char *copy_from_end, char *encoding, const char *errors)
{
  /* NOTE(sigmavirus24): In the event that there are \s in the string, we're
   * over-allocating here but that is okay since we're going to free shortly
   * after use.
   * The +1 is also necessary to ensure it's '\0' terminated.
   */
  ssize_t copy_max_length = (copy_from_end - copy_from_start) + 1;
  ssize_t copy_index = 0;
  ssize_t index;
  char *copy_to = calloc(copy_max_length, sizeof(char));
  PyObject *unicode;

  for (index = 0; index < (copy_max_length - 1); index++) {
      if (copy_from_start[index] == '\\') {
          index++;
      }
      copy_to[copy_index++] = copy_from_start[index];
  }
  unicode = PyUnicode_Decode(copy_to, copy_index, encoding, errors);
  free(copy_to);

  return unicode;
}

PyObject *
escape(PyObject* to_escape)
{
    PyObject *intermediately_escaped;
    PyObject *escaped;
#if IS_PY3
    /* We're operating on a bytes object and what the char*s treated as bytes
     * objects too.
     */
    char *build_value_format_string = "yy";
#else
    /* We're operating on a str object and what the char*s treated as str
     * objects too.
     */
    char *build_value_format_string = "ss";
#endif

    intermediately_escaped = PyObject_CallMethod(to_escape, "replace", build_value_format_string, "\\", "\\\\");
    if (!intermediately_escaped) {
        return NULL;
    }
    escaped = PyObject_CallMethod(intermediately_escaped, "replace", build_value_format_string, "\"", "\\\"");
    Py_DECREF(intermediately_escaped);
    return escaped;
}

int _find_key_value_separator(char **start, char *s_start, char *s_end) {
    char *pos;
    for(pos = *start; pos <= s_end; pos++) {
        switch(*pos) {
            case ' ':
            case '\t':
            case '\r':
            case '\n':
                break;
            case '=':
                if (pos[1] == '>') {
                    *start = pos + 2;
                    return 0;
                }
            default:
                if (PyErr_Occurred() == NULL){
                    PyErr_Format(PyExc_ValueError,                  
                            "Unexpected input after position %i, was expecting a =>, got %c", pos-s_start, *pos);                          
                }
                return 1;
        }
    }
    if (PyErr_Occurred() == NULL){
        PyErr_Format(PyExc_ValueError,                  
                "Unexpected end of input after position %i, was expecting a =>", pos-s_start);                          
    }
    return 1;
}
int _find_quoted(char **start_pos, char *s_start, char *s_end, char **token_start, char **token_end, int allow_null) {
    char *pos;
    int only_space = 1;

    *token_start = NULL;
    *token_end = NULL;

    for(pos = *start_pos; pos <= s_end; pos++) {
        // consume empty space
        switch(*pos) {
            case ' ':
            case '\t':
            case '\r':
            case '\n':
                break;
            case '"':
                // start of quoted token
                only_space = 0;
                *token_start = pos + 1;
                *token_end = strchr_unescaped(*token_start, s_end-(*token_start), '"');

                if (*token_end == NULL) {
                    if (PyErr_Occurred() == NULL){
                        PyErr_Format(PyExc_ValueError,                  
                                "Unexpected end of input after position %i, was expecting a quoted string.", pos-s_start);                          
                    }
                    return 1;
                }

                *start_pos = (*token_end) + 1;

                debug_print( "found token: pos[%c, %li], ks[%c, %li], ke[%c, %li]\n", **start_pos,  *start_pos-s_start, **token_start, *token_start-s_start, **token_end, *token_end-s_start);
                return 0;
            
            case 'N':
            case 'n':
                only_space = 0;
                if (allow_null) {
                    char *nullstr_uc = "NULL";
                    char *nullstr_lc = "null";
                    int is_null = 1;
                    for (int i = 1; i < 4; i++) {
                        is_null = is_null && (pos[i] == nullstr_uc[i] || pos[i] == nullstr_lc[i]);
                        if (!is_null) {
                            break;
                        }
                    }
                    if (is_null) {
                        *start_pos = pos + 4;
                        return 2; 
                    }
                }

            default:
                if (PyErr_Occurred() == NULL){
                    PyErr_Format(PyExc_ValueError,                  
                            "Unexpected end of input after position %i, was expecting a quoted string.", pos-s_start);
                }
                return 1;
        }
    }
    if (!only_space) {
        if (PyErr_Occurred() == NULL){
            PyErr_Format(PyExc_ValueError,                  
                    "Unexpected end of input after position %i, was expecting a quoted string.", pos-s_start);                          
        }

        return 1;
    }
    return 3;

}

int _find_comma_separator(char **s, char *s_start, char *s_end){
    int retval = 0;
    char * pos;
    for (pos = *s; pos < s_end; pos++) {
        switch(*pos) {
            case ' ':
            case '\t':
            case '\r':
            case '\n':
                break;
            case ',':
                if (retval) {
                    // double comma
                    if (PyErr_Occurred() == NULL){
                        PyErr_Format(PyExc_ValueError,                  
                                "Extra ',' at position %i found. Was expecting '\"'", pos-s_start);
                    }
                    return 2;
                }
                retval = 1;
                break;
            default:
                if (retval == 1) {
                    // a comma was found and this should be the start of a new key.
                    *s = pos;
                    return retval;
                }
                // Non-space found before comma
                if (PyErr_Occurred() == NULL){
                    PyErr_Format(PyExc_ValueError,                  
                            "Unexpected value '%c', %p found at position %i found. Was expecting ','", *pos, *pos, pos-s_start);
                }
                return 2;
        }
    }

    // only space
    *s = pos;
    return retval;
}

static PyObject *
_speedups_loads(PyObject *self, PyObject *args, PyObject *keywds)
{
  static char *keyword_argument_names[] = {"string", "encoding", "return_type", NULL};
  const char *errors = "strict";
  char *encoding = "utf-8";
  char *s_start, *s_end, *pos;
  Py_ssize_t s_length = 0;
  int null_value = 0, got_one = 0, need_one = 0;
  int is_dictionary = 0;
  char *key_start, *key_end, *value_start, *value_end;
  PyTypeObject *return_type = &PyDict_Type;
  PyObject *return_value, *key, *value;

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "s#|sO", keyword_argument_names, &s_start, &s_length, &encoding, &return_type)) {
    return NULL;
  }
  /* NOTE(sigmavirus24): Because we use `s#` to parse the input string, we
   * also need to pass s_length to get the length of the string because `s`
   * may have embedded null characters.
   * All of our tests presently pass but it's plausible that we could find
   * data with null characters inside and have to update this to match.
   * We need `s#` as a format argument here so we can receive both unicode and
   * bytes objects in char *s_start.
   */
  s_end = s_start+s_length;

  return_value = PyObject_CallObject((PyObject *) return_type, NULL);
  is_dictionary = PyDict_Check(return_value);

  pos = s_start;
  while (pos < s_end){
      key_start = NULL;
      key_end = NULL;
      value_start = NULL;
      value_end= NULL;
      null_value = 0;
      
      switch(_find_quoted(&pos, s_start, s_end, &key_start, &key_end, 0)){
          case 0:
              // valid key found
              debug_print( "found key: pos[%c, %li], ks[%c, %li], ke[%c, %li]\n", *pos,  pos-s_start, *key_start, key_start-s_start, *key_end, key_end-s_start);
              need_one = 0;
              break;
          case 3:
              // we got only space at this point
              if (got_one) {
                  if (need_one) {
                      if (PyErr_Occurred() == NULL){
                          PyErr_Format(PyExc_ValueError,                  
                                      "Unexpected end of input at position %i, was expecting '\"'.", s_length, '"');                          
                      }
                      goto _speedup_loads_cleanup_and_exit;
                  }
                  return return_value;
              } else {
                  // logic to return None
                  Py_DECREF(return_value);
                  Py_INCREF(Py_None);
                  return Py_None;
              }
          default:
              // exception set in _find_quoted
              goto _speedup_loads_cleanup_and_exit;
      }
      if (_find_key_value_separator(&pos, s_start, s_end)) {
          // error set in _find_key_value_separator
          goto _speedup_loads_cleanup_and_exit;
      }
      switch (_find_quoted(&pos, s_start, s_end, &value_start, &value_end, 1)){
          case 2:
              // NULL
              debug_print( "found null value: pos[%c, %li]\n", *pos,  pos-s_start);
              null_value = 1;
              break;
          case 0:
              // quoted value
              debug_print( "found value: pos[%c, %li], vs[%c, %li], ve[%c, %li]\n", *pos,  pos-s_start, *value_start, value_start-s_start, *value_end, value_end-s_start);
              null_value = 0;
              break;
        
          default:
              // error finding separator
              goto _speedup_loads_cleanup_and_exit;
              break; // never gonna get here
      }

      // handle key/value
      key = unescape(key_start, key_end, encoding, errors);
      if (key == NULL) {
          if (PyErr_Occurred() == NULL){
              PyErr_Format(PyExc_ValueError,                  
                      "Unexpected end of input at position %i, was expecting %c.", s_length, '"');                          
          }
          goto _speedup_loads_cleanup_and_exit;
      }
      if (null_value == 0) {
          // find and null terminate end of value
          value_end = strchr_unescaped(value_start, s_end-value_start, '"');
          value = unescape(value_start, value_end, encoding, errors);
      } else {
          Py_INCREF(Py_None);
          value = Py_None;
      }
      if (key == NULL || value == NULL) {
        goto _speedup_loads_cleanup_and_exit;
      }

      if (is_dictionary) {
          PyDict_SetItem(return_value, key, value);
      } else {
          PyList_Append(return_value, PyTuple_Pack(2, key, value));
      }

      Py_DECREF(key);
      Py_DECREF(value);
      key = NULL;
      value = NULL;
      
      switch (_find_comma_separator(&pos, s_start, s_end)) {
        case 0:
            // only space
            debug_print( "found only space: pos[%c, %li]\n", *pos,  pos-s_start);
            need_one = 0;
            break;
        case 1:
            // comma found
            // we expect to need an iteration
            debug_print( "found comma: pos[%c, %li]\n", *pos,  pos-s_start);
            need_one = 1;
            break;

        default:
            // found something other than leading space and a single comma
            goto _speedup_loads_cleanup_and_exit;
      }
  }

  if (need_one) {
      if (PyErr_Occurred() == NULL){
          PyErr_Format(PyExc_ValueError,                  
                      "Unexpected end of input at position %i, was expecting '\"'.", s_length, '"');                          
      }
      goto _speedup_loads_cleanup_and_exit;

  }
  return return_value;

_speedup_loads_cleanup_and_exit:
    Py_XDECREF(key);
    Py_XDECREF(value);
    Py_DECREF(return_value);
    return NULL;


}

#define COMMA ","
#define ARROW "=>"
#define EMPTY ""
#define S_NULL "NULL"
#define CITATION "\""

static PyObject *
_speedups_dumps(PyObject *self, PyObject *args, PyObject *keywds)
{
  static char *keyword_argument_names[] = {"obj", "key_map", "value_map", "encoding", "return_unicode", NULL};
  int i = 0;
  const char *errors = "strict";
  char *encoding = "utf-8";
  PyObject *obj, *list, *iter, *item;
  PyObject *return_unicode = Py_False;
  PyObject *key_map_callback = Py_None;
  Py_INCREF(Py_None);
  PyObject *value_map_callback = Py_None;
  Py_INCREF(Py_None);
  PyObject *unencoded_key, *unescaped_key, *key;
  PyObject *unencoded_value, *unescaped_value, *value;
  PyObject *result;
  PyObject *comma, *arrow, *empty, *s_null, *citation;
  PyObject *exception_string = NULL;
  PyObject *exception_string_format_args = NULL;
  Py_ssize_t list_len = 0;

  if (!PyArg_ParseTupleAndKeywords(args, keywds, "O|OOsO", keyword_argument_names, &obj, &key_map_callback, &value_map_callback, &encoding, &return_unicode)) {
    return NULL;
  }

  if (PyCallable_Check(key_map_callback)) {
      Py_INCREF(key_map_callback);
  }

  if (PyCallable_Check(value_map_callback)) {
      Py_INCREF(value_map_callback);
  }

  // return empty string if we got an empty dict
  empty = PyBytes_FromString(EMPTY);

  if (PyDict_Check(obj)) {
      list = PyDict_Items(obj);
  } else {
      list = obj;
      Py_INCREF(obj);
  }

  list_len = PyObject_Length(list);
  if (list_len <= 0) {
    return empty;
  }
  
  // create string constants
  comma = PyBytes_FromString(COMMA);
  arrow = PyBytes_FromString(ARROW);
  s_null = PyBytes_FromString(S_NULL);
  citation = PyBytes_FromString(CITATION);
  
  result = PyBytes_FromString(EMPTY);
  iter = PyObject_GetIter(list);

  while ((item = PyIter_Next(iter))) {
    // add comma (,)
    if (i > 0) {
      ConcatOrGotoCleanup(result, comma);
    }
    // add key
    ConcatOrGotoCleanup(result, citation);
    unencoded_key = PyTuple_GetItem(item, 0);

    if (key_map_callback != Py_None && PyCallable_Check(key_map_callback)) {
        unencoded_key = PyObject_CallObject(key_map_callback, PyTuple_Pack(1, unencoded_key));
    }

    if (PyUnicode_Check(unencoded_key)) {
        unescaped_key = PyUnicode_AsEncodedString(unencoded_key, encoding, errors);
    } else {
        if (PyBytes_Check(unencoded_key)) {
            unescaped_key = unencoded_key;
            Py_INCREF(unencoded_key);
        } else {
            unescaped_key = PyObject_Bytes(unencoded_key);
        }
    }

    key = escape(unescaped_key);
    Py_DECREF(unescaped_key);
    if (key == NULL) {
        goto _speedup_dumps_cleanup_and_exit;
    }

    unencoded_value = PyTuple_GetItem(item, 1);
    if (value_map_callback != Py_None && PyCallable_Check(value_map_callback)) {
        unencoded_value = PyObject_CallObject(value_map_callback, PyTuple_Pack(1, unencoded_value));
    }
    if (PyUnicode_Check(unencoded_value)) {
        unescaped_value = PyUnicode_AsEncodedString(unencoded_value, encoding, errors);
    } else {
        unescaped_value = unencoded_value;
        Py_INCREF(unencoded_value);
    }

    if (unescaped_value != Py_None) {
        value = escape(unescaped_value);
        Py_DECREF(unescaped_value);
        if (value == NULL) {
            goto _speedup_dumps_cleanup_and_exit;
        }
    } else {
        value = unescaped_value;
    }

    ConcatOrGotoCleanup(result, key);
    ConcatOrGotoCleanup(result, citation);
    // add arrow (=>)
    ConcatOrGotoCleanup(result, arrow);
    // add value or null
    if (value != Py_None) {
      if (!PyBytes_Check(value)) {
          exception_string = PyUnicode_FromString("value %r of %r is not a string");
          exception_string_format_args = PyTuple_Pack(2, value, key);
          PyErr_SetObject(PyExc_TypeError, PyUnicode_Format(exception_string, exception_string_format_args));
          Py_CLEAR(result);
          goto _speedup_dumps_cleanup_and_exit;
      }
      // add value
      ConcatOrGotoCleanup(result, citation);
      ConcatOrGotoCleanup(result, PyObject_Bytes(value));
      ConcatOrGotoCleanup(result, citation);
    } else {
      // add null
      ConcatOrGotoCleanup(result, empty);
      ConcatOrGotoCleanup(result, s_null);
      ConcatOrGotoCleanup(result, empty);

    }
    Py_DECREF(item);
    Py_DECREF(key);
    Py_DECREF(value);
    i++;
  }
_speedup_dumps_cleanup_and_exit:
  Py_DECREF(empty);
  Py_DECREF(comma);
  Py_DECREF(arrow);
  Py_DECREF(s_null);
  Py_DECREF(citation);
  Py_DECREF(iter);
  Py_DECREF(list);
  Py_XDECREF(value_map_callback);
  Py_XDECREF(key_map_callback);

  if (return_unicode == Py_True) {
      result = PyUnicode_FromEncodedObject(result, encoding, errors);
  }
  return result;
}


static PyMethodDef CPgHstoreMethods[] = {
    {"loads",  (PyCFunction)_speedups_loads, METH_VARARGS | METH_KEYWORDS,
     "Parse (decode) a postgres hstore string into an object."},
    {"dumps",  (PyCFunction)_speedups_dumps, METH_VARARGS | METH_KEYWORDS,
     "Dump (encode) a object into a postgres hstore string."},
    {NULL, NULL, 0, NULL}        /* Sentinel */
};

#if IS_PY3
static int pghstore_speedups_traverse(PyObject *m, visitproc visit, void *arg) {
    Py_VISIT(GETSTATE(m)->error);
    return 0;
}

static int pghstore_speedups_clear(PyObject *m) {
    Py_CLEAR(GETSTATE(m)->error);
    return 0;
}

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "pghstore._speedups",
    NULL,
    sizeof(struct module_state),
    CPgHstoreMethods,
    NULL,
    pghstore_speedups_traverse,
    pghstore_speedups_clear,
    NULL
};

PyMODINIT_FUNC
PyInit__speedups(void)
{
    PyObject *module;

    module = PyModule_Create(&moduledef);
    if (module == NULL) {
        return NULL;
    }

    return module;
}
#else
PyMODINIT_FUNC
init_speedups(void)
{
    (void) Py_InitModule("pghstore._speedups", CPgHstoreMethods);
}
#endif

int
main(int argc, char *argv[])
{
#if IS_PY3
    wchar_t *program = Py_DecodeLocale(argv[0], NULL);
    /* Pass program name to the Python interpreter */
    Py_SetProgramName(program);
#else
    Py_SetProgramName(argv[0]);
#endif

    /* Initialize the Python interpreter.  Required. */
    Py_Initialize();

#if IS_PY2
    /* Add a static module */
    init_speedups();
#endif

    return 0;
}
