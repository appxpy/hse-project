from flask import Flask, render_template, request
import ctypes
from math import copysign, fabs, floor, isfinite, modf


app = Flask(__name__)


def add(x, y):
    maxlen = max(len(x), len(y))
    x = x.zfill(maxlen)
    y = y.zfill(maxlen)
    result = ''
    carry = 0
    for i in range(maxlen - 1, -1, -1):
        r = carry
        r += 1 if x[i] == '1' else 0
        r += 1 if y[i] == '1' else 0
        # r can be 0,1,2,3 (carry + x[i] + y[i])
        # and among these, for r==1 and r==3 you will have result bit = 1
        # for r==2 and r==3 you will have carry = 1
        result = ('1' if r % 2 == 1 else '0') + result
        carry = 0 if r < 2 else 1
    if carry != 0:
        result = '1' + result
    return result.zfill(maxlen)


def float_to_bin_fixed(f):
    if not isfinite(f):
        return repr(f)  # inf nan

    sign = '-' * (copysign(1.0, f) < 0)
    frac, fint = modf(fabs(f))  # split on fractional, integer parts
    n, d = frac.as_integer_ratio()  # frac = numerator / denominator
    assert d & (d - 1) == 0  # power of two
    return (sign, f'{floor(fint):b}', f'{n:0{d.bit_length()-1}b}')


def custom_uint32(n):
    # переводим в двоичку, раскладываем по переменным
    frac, fint = modf(fabs(n))
    znak, integer_part, fractional_part = float_to_bin_fixed(n)
    # делаем знак более удобным для вывода инфы
    if znak == '':
        znak = (0, '+')
    else:
        znak = (1, '-')
    print(f"Двоичная запись числа: {integer_part}.{fractional_part}")
    # Убираем первую единицу в числовой части
    integer_part = integer_part[1:]
    print(f"Представляем число без первой значащей единицы: {integer_part}.{fractional_part}")
    # Считаем порядок
    order = len(integer_part)
    order_memory = bin(order + 127)[2:]
    print(f"""
Знак: {znak[1]}
Знак в памяти: {znak[0]}
Порядок: {order}
Порядок в памяти: {order_memory}
Мантисса: {integer_part + fractional_part}
Мантисса в памяти: {(integer_part + fractional_part).ljust(23, '0')}
""")
    mantissa = integer_part + fractional_part
    if len(mantissa) > 23:
        mantissa = add(mantissa[:23], '1')
    else:
        mantissa = mantissa.ljust(23, '0')
    return {'true_uint': bin(ctypes.c_uint32.from_buffer(ctypes.c_float(n)).value)[2:].zfill(32),
            'true_uint_64': bin(ctypes.c_uint64.from_buffer(ctypes.c_double(n)).value)[2:].zfill(64),
            'number': n,
            'number_uint': f"{znak[0]} {order_memory} {mantissa}",
            'number_uint_hex': hex(int(f"{znak[0]}{order_memory}{mantissa}", 2))[2:],
            'number_int': fint,
            'number_float': frac,
            'number_int_bin': integer_part,
            'number_float_bin': fractional_part,
            'number_sign': znak[1],
            'number_order': len(integer_part),
            'number_mantissa': integer_part + fractional_part,
            'number_sign_bin': znak[0],
            'number_order_bin': order_memory,
            'number_mantissa_bin': mantissa,
            }


def custom_uint32_backwards(n):
    if len(n) != 32:
        return {'error_binary': 'Длина числа не равна 32'}
    if n.replace("0", "").replace("1", "") != "":
        return {'error_binary': 'Число не является двоичным'}
    return {'number_backwards': ctypes.c_float.from_buffer(ctypes.c_uint32(int(f'0b{n}', 2))).value}


@app.route('/')
def index():
    number = request.args.get('number')
    try:
        float(number)
    except Exception:
        return render_template('index.html', error='Не число')
    data = custom_uint32(float(number))
    return render_template('index.html', **data, **custom_uint32_backwards(number))


app.run(host='0.0.0.0', port=80, debug=True)
