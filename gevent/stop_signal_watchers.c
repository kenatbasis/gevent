#ifdef Py_PYTHON_H
void dummy_handler(struct ev_loop *l, ev_signal *w, int revents) {
    printf("SIGTERM handler_b called in process %d\n", getpid());
    ev_break(l, EVBREAK_ALL);
}

static void gevent_stop_signal_watchers(struct ev_loop * loop) {
     // check if a signal handler exists
    struct sigaction sa;
    sigaction (SIGINT, NULL, &sa);
    printf("SIGINT handler address: 0x%lx\n", sa.sa_sigaction);

    sigaction (SIGPIPE, NULL, &sa);
    // python sets sigpipe to 0x1 by default and sigint to some crazy thing,
    // everything else is 0x0
    printf("SIGTERM handler address: 0x%lx\n", sa.sa_sigaction);
    
     
     // create and start a signal just to get a *next handle
     ev_signal signal_watcher;
     ev_signal_init(&signal_watcher, dummy_handler, SIGINT);
     ev_signal_start(loop, &signal_watcher);
 
     ev_signal * n = (ev_signal *)signal_watcher.next;
     ev_ref(loop);
     ev_signal_stop(loop, &signal_watcher);
     printf("stopped dummy signal\n");
 
     while(n) {
         printf("in loop\n");
         ev_ref(loop);
         ev_signal * m = (ev_signal *)n->next;
         ev_signal_stop(loop, n);
         n = m;
     }
}
#endif  /* Py_PYTHON_H */
