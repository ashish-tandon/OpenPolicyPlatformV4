import {
  View,
  Text,
  ScrollView,
  KeyboardAvoidingView,
  TouchableOpacity,
  TextInput,
  Image,
} from 'react-native';
import React, { useState } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import images from '../constants/images';
import { useAlert } from '../context/AlertProvider';

const PasswordSetup = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isValid, setIsValid] = useState({
    length: false,
    number: false,
    symbol: false,
  });
  const { showError, showSuccess } = useAlert();

  // Password validation rules
  const validatePassword = (pass) => {
    setIsValid({
      length: pass.length >= 8,
      number: /\d/.test(pass),
      symbol: /[!@#$%^&*(),.?":{}|<>]/.test(pass),
    });
  };

  const handleNext = () => {
    if (
      isValid.length &&
      isValid.number &&
      isValid.symbol &&
      password === confirmPassword
    ) {
      showSuccess('Password set successfully!');
      router.push('/welcome');
    } else {
      showError('Passwords do not match or requirements are not met.');
    }
  };

  return (
    <SafeAreaView className="bg-white h-full">
      <ScrollView contentContainerStyle={{ height: '100%' }}>
        <KeyboardAvoidingView behavior="padding" className="flex-1 px-6 pt-8">
          {/* Back Icon and Progress Bar */}
          <View className="flex-row items-center mb-10">
            <TouchableOpacity className="mr-9" onPress={() => router.back()}>
              <Ionicons name="chevron-back" size={24} color="black" />
            </TouchableOpacity>
            <View className="h-1 w-[202px] bg-gray-200 ml-9">
              <View className="h-1 bg-black w-full" />
            </View>
          </View>

          {/* Header */}
          <Text className="text-blue-300 text-center font-semibold mb-5 mt-8">
            OpenPolicy
          </Text>
          <Text className="text-2xl font-bold text-black text-center mb-10">
            One last step
          </Text>

          {/* Create Password */}
          <Text className="text-gray-500 mt-10 mb-7">Create Password</Text>
          <View className="flex-row items-center border border-b-gray-300 border-l-white border-r-white border-t-white px-3 mb-4">
            <TextInput
              secureTextEntry={!showPassword}
              value={password}
              onChangeText={(text) => {
                setPassword(text);
                validatePassword(text);
              }}
              placeholder="Enter your password"
              className="flex-1 py-2"
            />
            <TouchableOpacity onPress={() => setShowPassword(!showPassword)}>
              <Ionicons name={showPassword ? 'eye-off' : 'eye'} size={20} />
            </TouchableOpacity>
          </View>

          {/* Confirm Password */}
          <Text className="text-gray-500 mt-10 mb-7">Confirm Password</Text>
          <View className="flex-row items-center border border-b-gray-300 border-l-white border-r-white border-t-white px-3 mb-8">
            <TextInput
              secureTextEntry={!showConfirmPassword}
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              placeholder="Re-enter your password"
              className="flex-1 py-2 "
            />
            <TouchableOpacity
              onPress={() => setShowConfirmPassword(!showConfirmPassword)}
            >
              <Ionicons
                name={showConfirmPassword ? 'eye-off' : 'eye'}
                size={20}
              />
            </TouchableOpacity>
          </View>

          {/* Validation */}
          <View className="mb-8 flex-row items-center justify-center mt-5">
            <View className="flex-row">
              {isValid.length && (
                <Image source={images.check} resizeMode="contain" />
              )}
              <Text
                className={`text-sm mr-5 ${
                  isValid.length ? 'text-black-500' : 'text-gray-400'
                }`}
              >
                8 characters
              </Text>
            </View>
            <View className="flex-row">
              {isValid.symbol && (
                <Image source={images.check} resizeMode="contain" />
              )}
              <Text
                className={`text-sm mr-5 ${
                  isValid.symbol ? 'text-black-500' : 'text-gray-400'
                }`}
              >
                1 symbol
              </Text>
            </View>
            <View className="flex-row">
              {isValid.number && (
                <Image source={images.check} resizeMode="contain" />
              )}
              <Text
                className={`text-sm mr-5 ${
                  isValid.number ? 'text-black-500' : 'text-gray-400'
                }`}
              >
                1 number
              </Text>
            </View>
          </View>

          {/* Next Button */}
          <TouchableOpacity
            onPress={handleNext}
            className="bg-black py-5 rounded-full mt-5 "
          >
            <Text className="text-white text-center font-semibold">Next</Text>
          </TouchableOpacity>
        </KeyboardAvoidingView>
      </ScrollView>
    </SafeAreaView>
  );
};

export default PasswordSetup;
