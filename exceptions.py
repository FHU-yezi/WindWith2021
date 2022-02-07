class QueueFullException(Exception):
    """队列已满时抛出此错误
    """
    pass


class UserAlreadyExistsException(Exception):
    """用户已加入队列时抛出此错误
    """
    pass


class UserDoesNotExistException(Exception):
    """用户不存在时抛出此错误
    """
    pass


class UserBannedException(Exception):
    """用户被封禁时抛出此错误
    """
    pass


class QueueEmptyException(Exception):
    """队列已空时抛出此错误
    """
    pass


class UserDataDoesNotReadyException(Exception):
    """用户数据未就绪时抛出此错误
    """
    pass


class UserDataException(Exception):
    """用户数据异常时抛出此错误
    """
    pass

class GetUserBasicDataException(Exception):
    """获取用户基本信息出错时抛出此错误
    """
    pass


class GetUserArticleDataException(Exception):
    """获取用户文章信息出错时抛出此错误
    """
    pass


class GetUserWordCloudException(Exception):
    """获取用户词云出错时抛出此错误
    """
    pass