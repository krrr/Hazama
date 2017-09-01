#pragma once
#include <QDialog>
#include <QDateTime>

class QDateTimeEdit;

class DateTimeDialog : public QDialog {
public:
    DateTimeDialog(QDateTime dt, const QString &displayFmt, QWidget *parent=nullptr);
    static QDateTime getDateTime(QDateTime dt, const QString &displayFmt, QWidget *parent=nullptr);

private:
    QString format;
    QDateTimeEdit *dtEdit;
};
