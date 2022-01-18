class QueueFullException(Exception):
    """队列已满时抛出此错误
    """
    pass


class UserAlreadyExistsException(Exception):
    """用户已加入队列时抛出此错误
    """
    pass


class UserBannedException(Exception):
    """用户被封禁时抛出此错误
    """
    pass
