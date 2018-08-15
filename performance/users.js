let currentUser = 1;


function nextUser() {
    if (currentUser >= 90 ) {
        currentUser = 1;
    }
    currentUser++;
    var rstring =  "{\"username\":\"perf" + currentUser + "\",\"password\":\"default2018\"}";
    return {
        rstring
    };
}

export { nextUser };