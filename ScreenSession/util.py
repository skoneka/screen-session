
import subprocess,sys,os,pwd,getopt,glob,time,signal,shutil,tempfile,traceback,re,string,shlex

archiveend=''
import tempfile,pwd
tmpdir=os.path.join(tempfile.gettempdir(),'screen-session-'+pwd.getpwuid(os.geteuid())[0] )

def _timeout_command_split(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""
    import subprocess, datetime, os, time, signal
    cmd = shlex.split(command)
    start = datetime.datetime.now()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(0.0001)
        now = datetime.datetime.now()
        if (now - start).seconds> timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    return process.stdout.readlines()

def timeout_command_list(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""
    import subprocess, datetime, os, time, signal
    start = datetime.datetime.now()
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(0.0001)
        now = datetime.datetime.now()
        if (now - start).seconds> timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None
    return process.stdout.readlines()

def timeout_command(command, timeout):
    #return os.popen(command).readlines()
    global timeout_command
    timeout_command=_timeout_command_split
    return timeout_command(command,timeout)

def out(str,verbosity=0):
    sys.stdout.write(str+'\n')
    sys.stdout.flush()


def touch(fname, times = None):
    try:
        os.utime(fname,times)
    except:
        pass

def linkify(dir,dest,targ):
    try:
        cwd=os.getcwd()
    except:
        cwd=None
    os.chdir(dir)
    try:
        os.remove(targ)
    except:
        pass
    os.symlink(dest,targ)
    if cwd:
        try:
            os.chdir(cwd)
        except:
            pass

def requireme(home,projectsdir,file_in_session,full=False):
    global archiveend
    global tmpdir
    if os.path.isfile(os.path.join(home,projectsdir,file_in_session)):
        return
    else:
        fhead,ftail = os.path.split(file_in_session)
        unpackme(home,projectsdir,fhead,archiveend,tmpdir,full)

def unpackme(home,projectsdir,savedir,archiveend,tmpdir,full=False):
    import tarfile
    removeit(os.path.join(home,projectsdir,savedir))
    removeit(os.path.join(tmpdir,savedir))
    if os.path.exists(os.path.join(tmpdir,savedir)):
        removeit(os.path.join(tmpdir,savedir))
    if not os.path.exists(os.path.join(home,projectsdir,savedir+'__win'+archiveend)):
        raise IOError
    os.makedirs(os.path.join(tmpdir,savedir))
    t1 = tarfile.open(os.path.join(home,projectsdir,savedir+'__win'+archiveend),'r')
    t1.extractall(os.path.join(tmpdir,savedir))
    t1.close()
    if full:
        t2 = tarfile.open(os.path.join(home,projectsdir,savedir+'__data'+archiveend),'r')
        t2.extractall(os.path.join(tmpdir,savedir))
        t2.close()
    # taking care of old archive types
    if os.path.split(glob.glob(os.path.join(tmpdir,savedir,'*'))[0])[1]==savedir:
        os.symlink(os.path.join(tmpdir,savedir,savedir),os.path.join(home,projectsdir,savedir))
    else:
        os.symlink(os.path.join(tmpdir,savedir),os.path.join(home,projectsdir,savedir))



def removeit(path):
    try:
        shutil.rmtree(path)
    except:
        try:
            os.remove(path)
        except:
            pass
        pass

def remove(path):
    try:
        os.remove(path)
    except:
        try:
            shutil.rmtree(path)
        except:
            pass
        pass

def cleantmp(tmpdir,home,projectsdir,archiveend,blacklistfile,timeout):
    #cleanup old temporary files and directories
    ctime=time.time()
    files_all=glob.glob(os.path.join(home,projectsdir,'*'))
    files_archives=glob.glob(os.path.join(home,projectsdir,'*%s'%archiveend))
    files_remove=list(set(files_all)-set(files_archives)-set([os.path.join(home,projectsdir,blacklistfile)]))
    for file in files_remove:
        try:
            delta=ctime-os.path.getmtime(file)
        except:
            delta=timeout+1
        if delta > timeout: # if seconds passed since last modification
            removeit(file)
    files_remove=glob.glob(os.path.join(tmpdir,'*'))
    files_noremove=glob.glob(os.path.join(tmpdir,'___*'))
    files_remove=list(set(files_remove)-set(files_noremove))
    for file in files_remove:
        try:
            delta=ctime-os.path.getmtime(file)
        except:
            delta=timeout+1
        if delta > timeout: # if seconds passed since last modification
            removeit(file)

def archiveme(tmpdir,home,projectsdir,savedir,archiveend,savedir_real):
    import tarfile
    try:
        t1 = tarfile.open(os.path.join(home,projectsdir,"%s__win%s"%(savedir_real,archiveend)),'w:bz2')
        for f in glob.glob(os.path.join(home,projectsdir,savedir_real+'__tmp','win_*')):
            t1.add(f,os.path.split(f)[1])
            remove(f)
        t1.add(os.path.join(home,projectsdir,savedir_real+'__tmp','last_win'),'last_win')
        t1.close()
    except Exception,x:
        print(str(x))
        raise x
    
    try:
        t2 = tarfile.open(os.path.join(home,projectsdir,"%s__data%s"%(savedir_real,archiveend)),'w:bz2')
        for f in glob.glob(os.path.join(home,projectsdir,savedir_real+'__tmp','*')):
            t2.add(f,os.path.split(f)[1])
        t2.close()
    except Exception,x:
        print(str(x))
        raise x


def list_sessions(home,projectsdir,archiveend,match):
    if not match:
        match=''
    files=glob.glob(os.path.join(home,projectsdir,'*%s*__win%s'%(match,archiveend)))
    
    date_file_list=[]
    for file in files:
        # the tuple element mtime at index 8 is the last-modified-date
        stats = os.stat(file)
        # create tuple (year yyyy, month(1-12), day(1-31), hour(0-23), minute(0-59), second(0-59),
        # weekday(0-6, 0 is monday), Julian day(1-366), daylight flag(-1,0 or 1)) from seconds since epoch
        # note: this tuple can be sorted properly by date and time
        lastmod_date = time.localtime(stats[8])
        date_file_tuple = lastmod_date, file
        date_file_list.append(date_file_tuple)
    
    date_file_list.sort()
    
    if len(date_file_list)>0:
        out('There are saved sessions:')
    else:
        out('There are no saved sessions.')
    
    fileending_l=len(archiveend)+len('__win')
    for file in date_file_list:
        # extract just the filename
        file_name = os.path.split(file[1])[1]
        file_name = file_name[:len(file_name)-fileending_l]
        # convert date tuple to MM/DD/YYYY HH:MM:SS format
        file_date = time.strftime("%d/%m/%Y\t%H:%M:%S", file[0])
        out("  %s\t%s" % (file_date, file_name))
    
    if len(date_file_list)>0:
        out('%s saved sessions in %s'%(len(date_file_list),os.path.join(home,projectsdir)))

def find_in_path(file, path=None):
  """find_in_path(file[, path=os.environ['PATH']]) -> list

  Finds all files with a specified name that exist in the operating system's
  search path (os.environ['PATH']), and returns them as a list in the same
  order as the path.  Instead of using the operating system's search path,
  the path argument can specify an alternative path, either as a list of paths
  of directories, or as a single string seperated by the character os.pathsep.

  If you want to limit the found files to those with particular properties,
  use filter() or which()."""

  if path is None:
    path = os.environ.get('PATH', '')
  if type(path) is type(''):
    path = string.split(path, os.pathsep)
  return filter(os.path.exists,
                map(lambda dir, file=file: os.path.join(dir, file), path))

def which(file, mode=os.F_OK | os.X_OK, path=None):
  """which(file[, mode][, path=os.environ['PATH']]) -> list

  Finds all executable files in the operating system's search path
  (os.environ['PATH']), and returns them as a list in the same order as the
  path.  Like the UNIX shell command 'which'.  Instead of using the operating
  system's search path, the path argument can specify an alternative path,
  either as a list of paths of directories, or as a single string seperated by
  the character os.pathsep.

  Alternatively, mode can be changed to a different os.access mode to
  check for files or directories other than "executable files".  For example,
  you can additionally enforce that the file be readable by specifying
  mode = os.F_OK | os.X_OK | os.R_OK."""

  return filter(lambda path, mode=mode: os.access(path, mode),
                find_in_path(file, path))

