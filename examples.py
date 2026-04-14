aio_example = """
- Past Action Taken: GET_CHUNK, then I already obtained the chunk, so I will GET_DETAIL.
- Past Action Taken: GET_CHUNK, GET_DETAIL, then I will EVALUATE the summary.
- Past Action Taken: GET_CHUNK, GET_DETAIL, EVALUATE. The result seems not going well, then I will GET_CHUNK again.
- Past Action Taken: GET_CHUNK, GET_DETAIL, EVALUATE. The result seems going well, then I will TERMINATE the process.
- Past Action Taken: GET_CHUNK, GET_DETAIL, EVALUATE, ... ,GET_CHUNK, GET_DETAIL, EVALUATE. This is chunk 10 out of 10. I suppose to get more chunk but I retrieved the last chunk already. No more knowledge chunks available, so I will TERMINATE the process.\
- Past Action Taken: GET_CHUNK, GET_DETAIL, EVALUATE, ... ,GET_CHUNK, GET_DETAIL, EVALUATE, GET_DETAIL, EVALUATE, GET_DETAIL, EVALUATE, GET_DETAIL, EVALUATE. This is chunk 50 out of 78. But seems there are no additional useful information and the action has been repeated for several times. To avoid infinite loop, I will TERMINATE the process.
"""