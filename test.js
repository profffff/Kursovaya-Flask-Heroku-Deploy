function runaway(id) {
    alert('clear2');
    if (id.style.left == `${0}px`)
        id.style.left = 100 + 'px';
    else
     id.style.left = 0 + 'px';
}