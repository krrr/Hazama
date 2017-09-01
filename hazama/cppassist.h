#pragma once
#include <cmath>
#include <QString>
#include <QStringList>

inline
bool is_true(bool b) { return b; }

template<typename T1, typename T2>
bool contains(const T1 &container, const T2 &v) {
    return std::find(std::begin(container), std::end(container), v) != std::end(container);
}

// Similar to built-in round, but numbers like 1.5
// will be rounded to smaller one(1.0)."""
inline
int myRound(double x) {
    auto absx = std::abs(x);
    auto y = std::floor(x);
    if (absx - y > 0.5)
        y += 1.0;
    return std::copysign(y, x);
}

inline
QStringList rsplit(const QString &s, const QString &sep) {
    int i = s.length() - 1;
    while (s[i] != sep && i >= 0)
        i--;
    if (i < 0)
        return QStringList{s};
    return {s.left(i), s.right(s.length()-i-1)};
}

template<typename T>
struct Range {
    struct Iterator {
        T value, step;
        Iterator(T v, T s): value(v), step(s) {}
        const Iterator & operator++() { value+=step; return *this; }
        bool operator!=(const Iterator & o) { return o.value != value; }
        T operator*() const { return value; }
    };

    const T from, to, step;

    Range(const T from, const T to, const T step): from(from), to(to), step(step) {
        Q_ASSERT((from < to && step > 0) || (from > to && step < 0));
    }
    Iterator begin() const { return Iterator(from, step); }
    Iterator end() const { return Iterator(to, step); }
};

template<typename T>
Range<T> range(const T end) { return Range<T>(0, end, 1); }

template<typename T>
Range<T> range(const T begin, const T end) { return Range<T>(begin, end, 1); }

template<typename T>
Range<T> range(const T begin, const T end, const T step) { return Range<T>(begin, end, step); }
