// PBS python interface
// Author: Bas van der Vlies <bas.vandervlies@surfsara.nl>
// Date  : 04 Sep 2001
// Vers. : 1.0
// Desc. : This is a simple python wrapper for PBS.
//
// SVN info
//  $Id: pbs.i 522 2010-03-26 08:45:32Z bas $
//
%module pbs
%include "typemaps.i"

// %include pointer.i
// %include PBS.i

// header declarations
//
%{

#include "pbs_ifl.h"
#include "pbs_error.h"
#include "rm.h"
#include "log.h"

#define SARA_DEBUG 0

//extern int pbs_errno;

%}


#if defined(SWIGPYTHON)

// *****************************************************************
// Some IN typemaps from Python ---> C
//
/*
 * Convert Python batch status list to a valid C-linked list
*/
%typemap(in) struct batch_status *BATCH_STATUS {
  PyObject              *py_obj;
  struct batch_status   *ptr, *prev;
  char                  s[255];
  int                   i=0, size=0;

  // printf("Python --> C\n");

  if (SARA_DEBUG) printf("Converteren python -> c (struct batch_status *):\n");

  size = Get_List_Size($input);
  if (SARA_DEBUG) printf("\tSize of batch_status list: %d\n", size);
  
  if ( size == -1 ) {
    PyErr_SetString(PyExc_TypeError, "not a list");
    return NULL; 
  }
  // printf("Size = %d\n", size);

  if (SARA_DEBUG) printf("\t<Contents>\n");

  $1 = prev = NULL;
  for ( i=0; i < size; i++ ) {
    py_obj = PyList_GetItem($input, i);
    if (SWIG_ConvertPtr(py_obj, (void **) &ptr, SWIGTYPE_p_batch_status, 1)) {

       sprintf(s,"list item %d has wrong type", i);
       PyErr_SetString(PyExc_TypeError, s);
       return NULL;

       // This will skipp the wrong entry
       // continue;
    }

    /* 
     * Make first entry head of C linked list
    */ 
    if ( i == 0) { 
      $1 = ptr;
      ptr->next = prev;
    }
    else {
      prev->next = ptr;
      ptr->next = NULL;
    }

    if (SARA_DEBUG) printf("\t\t- %s\n", ptr->name);
    prev = ptr;

  } // end for

  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end struct batch_status *IN typemap


/*
 * Convert Python attrl list to a valid C-linked list
*/
%typemap(in) struct attrl *ATTRL {
  PyObject      *py_obj;
  struct attrl  *ptr, *prev;
  char          s[255];
  int           i=0, size=0;

  // printf("Python --> C\n");

  if (SARA_DEBUG) printf("Converteren python -> c (struct attrl *):\n");

  size = Get_List_Size($input);
  if (SARA_DEBUG) printf("\tSize of attrl List: %d\n", size);
  
  if ( size == -1 ) {
      PyErr_SetString(PyExc_TypeError, "not a list");
      return NULL; 
  }

  if (SARA_DEBUG) printf("\t<Contents>\n");

  $1 = prev = NULL;
  for ( i=0; i < size; i++ ) {
    py_obj = PyList_GetItem($input, i);
    if (SWIG_ConvertPtr(py_obj, (void **) &ptr, SWIGTYPE_p_attrl, 1)) {

      sprintf(s,"list item %d has wrong type", i);
      PyErr_SetString(PyExc_TypeError, s);
      return NULL;

      // This will skipp the wrong entry
      // continue;
    }

    /* 
     * Make first entry head of C linked list
    */ 
    if ( i == 0) { 
      $1 = ptr;
      ptr->next = prev;
    }
    else {
      prev->next = ptr;
      ptr->next = NULL;
    }
    if (SARA_DEBUG) printf("\t\t- %s\n", ptr->name);
    
    prev = ptr;

  } // end for
  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end struct attrl *IN typemap

/*
 * Convert Python attropl list to a valid C-linked list
*/
%typemap(in) struct attropl *ATTROPL {
  PyObject          *py_obj;
  struct attropl    *ptr, *prev;
  char              s[255];
  int               i=0, size=0;

  // printf("Python --> C\n");

  if (SARA_DEBUG) printf("Converteren python -> c (struct attropl *):\n");

  size = Get_List_Size($input);

  if (SARA_DEBUG) printf("\tSize attropl List: %d\n", size);

  if ( size == -1 ) {
    PyErr_SetString(PyExc_TypeError, "not a list");
    return NULL; 
  }
  //printf("Size = %d\n", size);

  if (SARA_DEBUG) printf("\t<Contents>\n");

  $1 = prev = NULL;
  for ( i=0; i < size; i++ ) {
    py_obj = PyList_GetItem($input, i);
    if (SWIG_ConvertPtr(py_obj, (void **) &ptr, SWIGTYPE_p_attropl, 1)) {

       sprintf(s,"list item %d has wrong type", i);
       PyErr_SetString(PyExc_TypeError, s);
       return NULL;

       // This will skipp the wrong entry
       // continue;
    }

    /* 
     * Make first entry head of C linked list
    */ 
    if ( i == 0) { 
      $1 = ptr;
      ptr->next = prev;
    }
    else {
      prev->next = ptr;
      ptr->next = NULL;
    }
    prev = ptr;

  } // end for
  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end struct attrl *IN typemap

%typemap(in) char **CHARCAST {
  int       i=0, size=0;
  PyObject  *py_obj;

  if (SARA_DEBUG) printf("Convert python -> c (char **):\n");

  size = Get_List_Size($input);

  if (SARA_DEBUG) printf("\tSize of List: %d\n", size);

  if ( size == -1 ) {
    PyErr_SetString(PyExc_TypeError, "not a list");
    return NULL; 
  }
  // printf("Size = %d\n", size);

  if (SARA_DEBUG) printf("\t<Contents>\n");

  $1 = (char **) malloc( (size+1) * sizeof(char *));
  for (i=0; i < size; i++) {
    py_obj = PyList_GetItem($input, i);
    if (PyString_Check(py_obj)) {
      $1[i] = PyString_AsString(py_obj);
      if (SARA_DEBUG) printf("%s", $1[i]);
    }
    else {
      PyErr_SetString(PyExc_TypeError, "not a list of strings");
      free($1);
      return NULL; 
    }
  } // end for
  $1[i] = 0;
  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end typemap char **IN

// *****************************************************************
// Some OUT typemaps from C ---> Python
//
%typemap(out) struct batch_status * {

  PyObject              *obj_batch;
  struct batch_status   *ptr;
  int                   i=0, len=0;

  // printf("Ja we are in bussniss\n");
  if (SARA_DEBUG) printf("Converteren c (struct batch_status *) -> python:\n");
 
  // Deterime length of list
  //
  ptr = $1;
  while (ptr != NULL) {
    len++;
    ptr = ptr->next;
  }
  $result = PyList_New(len);

  if (SARA_DEBUG) printf("\tSize of List: %d\n", len);

  // Make a list of batch_status pointers
  //
  if (SARA_DEBUG) printf("\t<Contents>\n");
  ptr = $1;
  for (i=0; i < len; i++) {
    obj_batch = SWIG_NewPointerObj((void *)ptr, SWIGTYPE_p_batch_status,0); 
    PyList_SetItem($result, i, obj_batch);
    if (SARA_DEBUG)  {
        printf("\t\t- %s\n", ptr->name);
    }
    ptr = ptr->next;
  }

  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end typemap struct batch_status *

%typemap(out) struct attrl * {
  PyObject      *obj_batch;
  struct attrl  *ptr;
  int           i=0, len=0;

  if (SARA_DEBUG) printf("Converteren c (struct attrl *) -> python:\n");

  ptr = $1;
  while (ptr != NULL) {
    len++;
    ptr = ptr->next;
  }
  $result = PyList_New(len);

  if (SARA_DEBUG) printf("\tSize of List: %d\n", len);

  if (SARA_DEBUG) printf("\t<Contents>\n");
  ptr = $1;
  for (i=0; i < len; i++) {
    obj_batch = SWIG_NewPointerObj((void *)ptr, SWIGTYPE_p_attrl,1); 
    PyList_SetItem($result, i, obj_batch);
    if (SARA_DEBUG) printf("\t\t- %s\n", ptr->name);
    ptr = ptr->next;
  }
  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end typemap struct attrl *

%typemap(out) struct attropl * {
  PyObject          *obj_batch;
  struct attropl    *ptr;
  int               i=0, len=0;

  if (SARA_DEBUG) printf("Converteren c (struct attropl *) -> python:\n");
  
  ptr = $1;
  while (ptr != NULL) {
    len++;
    ptr = ptr->next;
  }
  $result = PyList_New(len);
  if (SARA_DEBUG) printf("\tSize of List: %d\n", len);

  if (SARA_DEBUG) printf("\t<Contents>\n");
  ptr = $1;
  for (i=0; i < len; i++) {
    obj_batch = SWIG_NewPointerObj((void *)ptr, SWIGTYPE_p_attropl,1); 
    PyList_SetItem($result, i, obj_batch); 
    ptr = ptr->next;
  }
  if (SARA_DEBUG) printf("\t</Contents>\n");
} // end typemap struct attropl *

// Convert C (char **) to Python List
//
%typemap(out) char ** {
   int len=0, i;

   if (SARA_DEBUG) 
     printf("Converteren char ** -> python list\n");


   if ($1 == NULL) 
     $result = PyList_New(0);
   else {
     while ($1[len]) 
       len++;
   }

   if (SARA_DEBUG) 
     printf("\tSize of List: %d\n", len);

   $result = PyList_New(len);
   if (SARA_DEBUG) 
     printf("\t<Contents>\n");
   for (i=0; i < len; i++ ) {
      PyList_SetItem($result, i , PyString_FromString($1[i])); 
      if (SARA_DEBUG) 
        printf("\t\t- %s\n", $1[i]);
   }
   if (SARA_DEBUG) 
     printf("\t</Contents>\n");
} // end typemap char **pbs_selectjob

// *****************************************************************
// Some freearg typemaps 
//
%typemap(freearg) char ** {
  free( (char *) $1);
}

#endif 

// *****************************************************************
// Some Functions used by all C-structs typemaps
//

%{
int Get_List_Size(PyObject *src)
{
  if (PyList_Check(src))
    return(PyList_Size(src));

  /* check if valid NULL pointer */
  if ( PyString_Check(src) ) {
    if ( ! strcmp(PyString_AsString(src), "NULL") )
      return(0);
  }
  return(-1);

} // end Get_List_Size()

%}


// *****************************************************************
// These C-functions are the constructurs for the different C-structs 
//
/*
 * Make some default constructors for the various structs
*/
%inline %{

// The default constructor for struct attrl
//
struct attrl *new_attrl(int number)
{
  struct attrl *ptr;
  struct attrl *prev, *current;
  int i;

  /* 
    allocate memory as a one block is handy for Python scripts 
    and fill in the next fields so it also works for the C-library
  */
  printf("basje \n");
  ptr = (struct attrl *) malloc(number * sizeof(struct attrl));

  prev = NULL;
  current = ptr + (number - 1);
  for (i=0; i < number; i++)
  { 
    printf("constructor called\n");
    current->name     = (char *) malloc(MAXNAMLEN * sizeof(char));
    current->resource = (char *) malloc(MAXNAMLEN * sizeof(char));
    current->value    = (char *) malloc(MAXNAMLEN * sizeof(char));

    bzero( (void*) current->name, sizeof(current->name));
    bzero( (void*) current->resource, sizeof(current->resource));
    bzero( (void*) current->value, sizeof(current->value));

    current->next     = prev;
    prev = current;
    current--;
  }
  return (struct attrl *)ptr;

} // end new_attrl()



// The default constructor for struct attropl
//
struct attropl *new_attropl(int number)
{
  struct attropl *ptr;
  struct attropl *prev, *current;
  int i;

  /* 
    allocate memory as a one block is handy for Python scripts 
    and fill in the next fields so it also works for the C-library
  */
  ptr = (struct attropl *) malloc(number * sizeof(struct attropl));

  prev = NULL;
  current = ptr + (number - 1);
  for (i=0; i < number; i++)
  { 
    printf("constructor called\n");
    current->name     = (char *) malloc(MAXNAMLEN * sizeof(char));
    current->resource = (char *) malloc(MAXNAMLEN * sizeof(char));
    current->value    = (char *) malloc(MAXNAMLEN * sizeof(char));

    bzero( (void*) current->name, sizeof(current->name));
    bzero( (void*) current->resource, sizeof(current->resource));
    bzero( (void*) current->value, sizeof(current->value));
    // current->op = 0;

    current->next     = prev;
    prev = current;
    current--;
  }
  return (struct attropl *)ptr;

} // end new_attropl()

/* Not used only returned */
struct batch_status *new_batch_status()
{
   struct batch_status *ptr;

   ptr = (struct batch_status *) malloc(sizeof(struct batch_status));
   return (struct batch_status *)ptr;
} // end new struct batch_status

int get_error()
{
   char *errmsg;

   errmsg = pbse_to_txt(pbs_errno);
   if (SARA_DEBUG)
   {
      printf("Bas = %d\n", pbs_errno);
      printf("Bas = %d, text = %s\n", pbs_errno, errmsg);
   }
   return (pbs_errno);
}


%}  // end %inline functions

%include <carrays.i>
%array_class(struct attrl, attrlArray);


// *****************************************************************
// Here the Python shadow class is generated. We have added some
// stuff here to extend the python classes.
//
%nodefault;
// %include "pbs_python.h"
%include "pbs_ifl.h"
%include "rm.h"
%include "log.h"


// Iets van uhhh..... obsolete
// %ignore pbs_errno;
//%include <pbs_error.h>


/*
%feature("shadow") attrl::__str__ {
  def __str__(self): print self.name + self.value;
}
%extend attrl {
  void __str__();
}
*/

/* not used
%extend batch_status {
  ~batch_status() {
  	if (SARA_DEBUG)
      printf("Bas free batch_status\n");
  	free(self);
  }
}
*/

%extend attrl {
  char *__str__() {
    static char temp[4 * MAXNAMLEN] ;
    snprintf(temp, sizeof(temp), "(%s,%s,%s)", 
      self->name, self->resource, self->value);
    
    return &temp[0];
  }

/*
 * For swig 1.3.29-2.1 we must create a destructor, but 
 * do not free anything pbs_statfree must do it
*/
  ~attrl() {
    if (SARA_DEBUG)
       printf("Bas free attrl\n");

    /*
  	free(self);
    */
  }
}

%extend attropl {
  char *__str__() {
    static char temp[4 * MAXNAMLEN] ;
    snprintf(temp, sizeof(temp), "(%s,%s,%s)", 
      self->name, self->resource, self->value);
    
    return &temp[0];
  }

/*
 * For swig 1.3.29-2.1 we must create a destructor, but 
 * do not free anything pbs_statfree must do it
*/
  ~attropl() {
    if (SARA_DEBUG)
       printf("Bas free attropl\n");

    /*
  	free(self);
    */
  }
}


%shadow "resmom.py"
%shadow "version.py"
%shadow "errors.py"
