def average(numbers):
    """
    计算数字列表的平均值。

    Args:
        numbers: 数字列表，如 [1, 2, 3, 4, 5]

    Returns:
        float: 所有数字的平均值

    Raises:
        ValueError: 当输入列表为空时抛出
        TypeError: 当输入不是列表时抛出
    """
    # 类型检查
    if not isinstance(numbers, list):
        raise TypeError("输入必须是列表类型")

    # 空列表检查
    if len(numbers) == 0:
        raise ValueError("列表不能为空")

    # 计算平均值
    return sum(numbers) / len(numbers)


if __name__ == "__main__":
    # 正常情况
    print(average([1, 2, 3, 4, 5]))  # 输出: 3.0

    # 单元素
    print(average([42]))  # 输出: 42.0

    # 浮点数列表
    print(average([1.5, 2.5, 3.0]))  # 输出: 2.333...

    # 异常处理示例
    try:
        average([])
    except ValueError as e:
        print(f"错误: {e}")  # 输出: 错误: 列表不能为空
